"""
LangGraph Workflow — The main orchestration graph.

This is the heart of the application. It defines a simple, linear graph:

    User Goal → Planner → Execution → Analysis → Report

No loops. No reflection. No complexity.
Just a clean pipeline that transforms a user's goal into a security report.
"""

import json
import logging
from typing import Callable
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from backend.graph.state import ReconState
from backend.agents.planner import PlannerAgent
from backend.agents.analysis import AnalysisAgent
from backend.agents.report import ReportAgent
from backend.execution.executor import ExecutionEngine
from backend.schemas import (
    ReconPlan, ToolResult, AnalysisResult, ScanStatus, ProgressUpdate
)



def _get_callback(scan_id: str):
    """Look up the progress callback from the global registry in routes.
    Avoids passing callables through LangGraph state."""
    try:
        from backend.api.routes import _scan_callbacks
        return _scan_callbacks.get(scan_id)
    except Exception:
        return None


async def _broadcast(scan_id: str, status: ScanStatus, stage: str, message: str,
                     progress: int, tool: str = ""):
    """Lookup callback and broadcast a ProgressUpdate."""
    cb = _get_callback(scan_id)
    if cb:
        await cb(ProgressUpdate(
            scan_id=scan_id, status=status, stage=stage,
            tool=tool, message=message, progress_percent=progress,
        ))


# ============================================================
# Graph Node Functions
# ============================================================

async def planner_node(state: ReconState) -> dict:
    """
    Node 1: Plan the reconnaissance.
    Uses the Planner Agent (LLM) to decide what to do.
    """
    scan_id = state["scan_id"]
    try:
        logger.info(f"Invoking AI PlannerAgent...")
        await _broadcast(scan_id, ScanStatus.PLANNING, "planner",
                         "🧠 AI Planner is generating your recon strategy...", 8)
        planner = PlannerAgent()
        plan = await planner.plan(state["target"], state["objective"])
        stage_names = [s.stage.value for s in plan.plan]
        logger.info("Planner generated plan successfully.")
        await _broadcast(scan_id, ScanStatus.PLANNING, "planner",
                         f"✅ Plan ready: {len(plan.plan)} stages — {', '.join(stage_names)}", 15)
        return {
            "plan": plan.model_dump(),
            "status": ScanStatus.PLANNING.value,
        }
    except Exception as e:
        await _broadcast(scan_id, ScanStatus.FAILED, "planner", f"❌ Planner failed: {e}", 0)
        return {
            "error": f"Planner failed: {str(e)}",
            "status": ScanStatus.FAILED.value,
        }


async def execution_node(state: ReconState) -> dict:
    """
    Node 2: Execute the plan.
    This is NOT an LLM node — it runs real tools via subprocess.
    """
    scan_id = state["scan_id"]
    try:
        plan = ReconPlan(**state["plan"])
        total_tools = sum(len(s.tools) for s in plan.plan)
        logger.info("Executing recon tools...")
        await _broadcast(scan_id, ScanStatus.EXECUTING, "execution",
                         f"🔧 Starting {len(plan.plan)} stage(s), {total_tools} tool(s) total...", 20)

        # Build callback using the registry
        cb = _get_callback(scan_id)
        engine = ExecutionEngine(progress_callback=cb)

        results = await engine.execute(plan, scan_id)
        logger.info("Execution complete.")
        await _broadcast(scan_id, ScanStatus.EXECUTING, "execution",
                         f"✅ All tools complete. {len(results)} result sets collected.", 60)
        return {
            "tool_results": [r.model_dump() for r in results],
            "status": ScanStatus.EXECUTING.value,
        }
    except Exception as e:
        await _broadcast(scan_id, ScanStatus.FAILED, "execution", f"❌ Execution failed: {e}", 0)
        return {
            "tool_results": [],
            "error": f"Execution failed: {str(e)}",
            "status": ScanStatus.FAILED.value,
        }


async def rag_node(state: ReconState) -> dict:
    """
    Node 2.5: Retrieve relevant security context via RAG.
    Runs between execution and analysis to enrich findings.
    """
    scan_id = state["scan_id"]
    try:
        logger.info("Querying local ChromaDB RAG...")
        await _broadcast(scan_id, ScanStatus.ANALYZING, "rag",
                         "🔍 Querying local security knowledge base (RAG)...", 65)
        from backend.rag.retriever import RAGRetriever
        retriever = RAGRetriever()
        results = [ToolResult(**r) for r in state.get("tool_results", [])]
        queries = []
        for r in results:
            if r.category == "vulnerability":
                queries.extend(r.results[:10])
            elif r.category == "technology":
                queries.extend(r.results[:5])
        queries.append(state["target"])
        context = await retriever.retrieve(queries)
        logger.info("RAG context query complete.")
        await _broadcast(scan_id, ScanStatus.ANALYZING, "rag",
                         f"✅ RAG context retrieved ({len(context)} bytes of CVE/CWE data).", 70)
        return {"rag_context": context}
    except Exception:
        return {"rag_context": ""}


async def analysis_node(state: ReconState) -> dict:
    """
    Node 3: Analyze results.
    Uses the Analysis Agent (LLM) to correlate and explain findings.
    """
    scan_id = state["scan_id"]
    try:
        logger.info("Invoking Analysis Agent...")
        await _broadcast(scan_id, ScanStatus.ANALYZING, "analysis",
                         "🤖 AI Analyst is correlating findings and enriching with CVE data...", 75)
        analyzer = AnalysisAgent()
        results = [ToolResult(**r) for r in state.get("tool_results", [])]
        analysis = await analyzer.analyze(
            target=state["target"],
            results=results,
            rag_context=state.get("rag_context", ""),
        )
        logger.info("Analysis complete.")
        await _broadcast(scan_id, ScanStatus.ANALYZING, "analysis",
                         f"✅ Analysis complete: {len(analysis.findings)} findings, {len(analysis.unique_subdomains)} subdomains found.", 85)
        return {
            "analysis": analysis.model_dump(),
            "status": ScanStatus.ANALYZING.value,
        }
    except Exception as e:
        await _broadcast(scan_id, ScanStatus.FAILED, "analysis", f"❌ Analysis failed: {e}", 0)
        return {
            "error": f"Analysis failed: {str(e)}",
            "status": ScanStatus.FAILED.value,
        }


async def report_node(state: ReconState) -> dict:
    """
    Node 4: Generate report.
    Uses the Report Agent (LLM) to create executive and technical reports.
    """
    scan_id = state["scan_id"]
    try:
        logger.info("Invoking Report Agent...")
        await _broadcast(scan_id, ScanStatus.REPORTING, "report",
                         "📝 AI Reporter is writing the final executive & technical report...", 90)
        reporter = ReportAgent()
        plan = ReconPlan(**state["plan"])
        results = [ToolResult(**r) for r in state.get("tool_results", [])]
        analysis = AnalysisResult(**state.get("analysis", {}))
        report = await reporter.generate(
            target=state["target"],
            plan=plan,
            results=results,
            analysis=analysis,
        )
        logger.info("Report complete.")
        await _broadcast(scan_id, ScanStatus.REPORTING, "report",
                         "✅ Report generation complete.", 98)
        return {
            "report": report.model_dump(),
            "status": ScanStatus.COMPLETED.value,
        }
    except Exception as e:
        await _broadcast(scan_id, ScanStatus.FAILED, "report", f"❌ Report failed: {e}", 0)
        return {
            "error": f"Report generation failed: {str(e)}",
            "status": ScanStatus.FAILED.value,
        }


# ============================================================
# Build the Graph
# ============================================================

def build_recon_graph() -> StateGraph:
    """
    Build the LangGraph workflow.
    
    Simple linear pipeline:
    
        START → planner → execution → rag → analysis → report → END
    
    No loops. No conditionals. No complexity.
    """
    # Create the graph with our state schema
    graph = StateGraph(ReconState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("execution", execution_node)
    graph.add_node("rag", rag_node)
    graph.add_node("analysis", analysis_node)
    graph.add_node("report", report_node)

    # Define the linear flow
    graph.set_entry_point("planner")
    graph.add_edge("planner", "execution")
    graph.add_edge("execution", "rag")
    graph.add_edge("rag", "analysis")
    graph.add_edge("analysis", "report")
    graph.add_edge("report", END)

    # Compile the graph
    return graph.compile()


# Create a singleton compiled graph
recon_workflow = build_recon_graph()
