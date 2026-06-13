"""
API Routes — All FastAPI endpoints.

Endpoints:
- POST /api/scan          — Start a new reconnaissance scan
- GET  /api/scan/{id}     — Get scan status and results
- GET  /api/scans         — List all scans
- POST /api/chat          — Chat with AI about scan results
- GET  /api/tools         — List available tools
- GET  /api/scan/{id}/report — Get the generated report
- GET  /api/compare/{target} — Compare scans for a target
"""

import json
import uuid
from datetime import datetime, timezone
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from langchain_core.prompts import ChatPromptTemplate

from backend.schemas import (
    ScanRequest, ScanResponse, ScanStatus, ChatRequest, ChatMessage,
    ProgressUpdate, ReconPlan, ToolResult, AnalysisResult, ReconReport,
)
from backend.config import settings
from backend.utils.llm import get_llm
from backend.tools import get_available_tools, get_all_tool_names
from backend.database.db import (
    save_scan, get_scan, get_all_scans, get_scans_for_target,
    save_chat_message, get_chat_history, delete_scan, ScanRecord,
)
from backend.graph.workflow import recon_workflow
import logging

import asyncio

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)



# ============================================================
# Progress streaming: active WS connections + replay buffer
# ============================================================

# scan_id -> list of active WebSocket connections
active_connections: dict[str, list[WebSocket]] = {}

# scan_id -> buffered updates (replayed when a new WS connects mid-scan)
progress_buffer: dict[str, list[dict]] = {}


async def broadcast_progress(update: ProgressUpdate):
    """Send a progress update to all connected WebSocket clients for this scan.
    Also buffers it so new connections can replay all past events."""
    scan_id = update.scan_id
    payload = update.model_dump()
    payload["timestamp"] = payload.get("timestamp") or __import__("datetime").datetime.utcnow().isoformat()

    # Buffer the update for late-joining WebSocket clients
    if scan_id not in progress_buffer:
        progress_buffer[scan_id] = []
    progress_buffer[scan_id].append(payload)

    # Send to all active connections
    if scan_id in active_connections:
        dead = []
        for ws in active_connections[scan_id]:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            active_connections[scan_id].remove(ws)


# ============================================================
# Scan Endpoints
# ============================================================

@router.post("/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest):
    """
    Start a new reconnaissance scan.
    Creates a scan record and kicks off the LangGraph workflow.
    """
    scan_id = str(uuid.uuid4())[:8]

    # Save initial scan record
    scan = ScanRecord(
        id=scan_id,
        target=request.target,
        objective=request.objective,
        status=ScanStatus.PENDING.value,
    )
    await save_scan(scan)

    # Run the workflow in the background
    asyncio.create_task(_run_scan(scan_id, request.target, request.objective))

    return ScanResponse(
        scan_id=scan_id,
        status=ScanStatus.PENDING,
        message=f"Scan started for {request.target}",
    )


# Global callback registry — keyed by scan_id
# This avoids passing callables through LangGraph state (which strips them)
_scan_callbacks: dict[str, any] = {}


async def _run_scan(scan_id: str, target: str, objective: str):
    """Background task that runs the full LangGraph workflow."""
    # Register callback in global registry so workflow nodes can find it by scan_id
    
    try:
        # Update status and send first event
        scan = await get_scan(scan_id)
        if scan:
            scan.status = ScanStatus.PLANNING.value
            await save_scan(scan)

        await broadcast_progress(ProgressUpdate(
            scan_id=scan_id, status=ScanStatus.PLANNING,
            stage="planner", message="🧠 AI Planner is designing reconnaissance strategy...",
            progress_percent=5,
        ))

        # Build initial state (no callback here - use registry instead)
        initial_state = {
            "scan_id": scan_id,
            "target": target,
            "objective": objective,
            "status": ScanStatus.PENDING.value,
            "error": "",
            "plan": {},
            "tool_results": [],
            "rag_context": "",
            "analysis": {},
            "report": {},
        }

        # Run the LangGraph workflow
        final_state = await recon_workflow.ainvoke(initial_state)

        # Save final results to database
        scan = await get_scan(scan_id)
        if scan:
            scan.status = final_state.get("status", ScanStatus.COMPLETED.value)
            scan.plan_json = json.dumps(final_state.get("plan", {}))
            scan.results_json = json.dumps(final_state.get("tool_results", []))
            scan.analysis_json = json.dumps(final_state.get("analysis", {}))
            scan.report_json = json.dumps(final_state.get("report", {}))
            scan.completed_at = datetime.now(timezone.utc)

            # Count total findings
            analysis = final_state.get("analysis", {})
            scan.total_findings = len(analysis.get("findings", []))

            await save_scan(scan)

            # Broadcast completion
            await broadcast_progress(ProgressUpdate(
                scan_id=scan_id,
                status=ScanStatus.COMPLETED,
                message="Scan completed!",
                progress_percent=100,
            ))

    except Exception as e:
        # Update scan as failed
        scan = await get_scan(scan_id)
        if scan:
            scan.status = ScanStatus.FAILED.value
            await save_scan(scan)

        await broadcast_progress(ProgressUpdate(
            scan_id=scan_id,
            status=ScanStatus.FAILED,
            message=f"Scan failed: {str(e)}",
        ))
    finally:
        # Clean up callback registry after scan ends
        


@router.get("/scan/{scan_id}")
async def get_scan_status(scan_id: str):
    """Get the current status and results of a scan."""
    scan = await get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {
        "scan_id": scan.id,
        "target": scan.target,
        "objective": scan.objective,
        "status": scan.status,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        "total_findings": scan.total_findings,
        "plan": json.loads(scan.plan_json) if scan.plan_json else {},
        "results": json.loads(scan.results_json) if scan.results_json else [],
        "analysis": json.loads(scan.analysis_json) if scan.analysis_json else {},
        "report": json.loads(scan.report_json) if scan.report_json else {},
    }


@router.get("/scans")
async def list_scans():
    """List all scans, newest first."""
    scans = await get_all_scans()
    return [
        {
            "scan_id": s.id,
            "target": s.target,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "total_findings": s.total_findings,
        }
        for s in scans
    ]


@router.get("/scan/{scan_id}/report")
async def get_report(scan_id: str):
    """Get the generated report for a scan."""
    scan = await get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    report = json.loads(scan.report_json) if scan.report_json else {}
    if not report:
        raise HTTPException(status_code=404, detail="Report not generated yet")

    return report


@router.get("/compare/{target}")
async def compare_scans(target: str):
    """Compare scans for the same target to see what changed."""
    scans = await get_scans_for_target(target)

    if len(scans) < 2:
        return {
            "message": "Need at least 2 scans to compare",
            "scans_available": len(scans),
        }

    # Compare the two most recent scans
    current = scans[0]
    previous = scans[1]

    current_analysis = json.loads(current.analysis_json) if current.analysis_json else {}
    previous_analysis = json.loads(previous.analysis_json) if previous.analysis_json else {}

    current_subs = set(current_analysis.get("unique_subdomains", []))
    previous_subs = set(previous_analysis.get("unique_subdomains", []))

    return {
        "target": target,
        "current_scan": current.id,
        "previous_scan": previous.id,
        "current_date": current.created_at.isoformat() if current.created_at else None,
        "previous_date": previous.created_at.isoformat() if previous.created_at else None,
        "new_subdomains": list(current_subs - previous_subs),
        "removed_subdomains": list(previous_subs - current_subs),
        "current_findings": current.total_findings,
        "previous_findings": previous.total_findings,
        "findings_change": current.total_findings - previous.total_findings,
    }


# ============================================================
# Chat Endpoint
# ============================================================

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with the AI about scan results.
    Uses scan context for relevant answers.
    """
    # Get scan context if a scan_id is provided
    context = ""
    if request.scan_id:
        scan = await get_scan(request.scan_id)
        if scan:
            analysis = json.loads(scan.analysis_json) if scan.analysis_json else {}
            report = json.loads(scan.report_json) if scan.report_json else {}
            context = (
                f"Target: {scan.target}\n"
                f"Status: {scan.status}\n"
                f"Analysis: {json.dumps(analysis, indent=2)[:3000]}\n"
                f"Report summary: {report.get('executive_summary', 'Not available')}\n"
            )

    # Save user message
    logger.info(f"[Chat] User message for scan {request.scan_id}: {request.message}")
    await save_chat_message(request.scan_id, "user", request.message)

    # Generate AI response
    llm = get_llm(temperature=0.3, force_json=False)

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a cybersecurity assistant. Answer questions about "
            "reconnaissance scan results. Be specific and actionable.\n\n"
            "Scan Context:\n{context}"
        )),
        ("human", "{message}"),
    ])

    chain = prompt | llm
    response = await chain.ainvoke({
        "context": context or "No scan context available. Answer generally.",
        "message": request.message,
    })

    # Save assistant message
    logger.info(f"[Chat] AI Response for scan {request.scan_id}: {response.content[:100]}...")
    await save_chat_message(request.scan_id, "assistant", response.content)

    return ChatMessage(
        role="assistant",
        content=response.content,
        scan_id=request.scan_id,
    )


# ============================================================
# Tools Endpoint
# ============================================================

@router.get("/tools")
async def list_tools():
    """List all registered tools and their availability."""
    available = get_available_tools()
    all_tools = get_all_tool_names()

    return {
        "available": available,
        "all": all_tools,
        "total_available": len(available),
        "total_registered": len(all_tools),
    }


# ============================================================
# WebSocket for Live Progress
# ============================================================

@router.websocket("/ws/{scan_id}")
async def websocket_progress(websocket: WebSocket, scan_id: str):
    await websocket.accept()
    if scan_id not in active_connections:
        active_connections[scan_id] = []
    active_connections[scan_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        if scan_id in active_connections:
            active_connections[scan_id].remove(websocket)
            if not active_connections[scan_id]:
                del active_connections[scan_id]
