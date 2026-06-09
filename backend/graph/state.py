"""
LangGraph State — Defines what data flows through the graph.

This is the shared state that every node in the graph can read and write.
It tracks the scan from start (user goal) to finish (final report).
"""

from typing import Annotated, Any
from typing_extensions import TypedDict

from backend.schemas import (
    ReconPlan, ToolResult, AnalysisResult, ReconReport, ScanStatus
)


class ReconState(TypedDict):
    """
    The state that flows through the LangGraph workflow.
    
    Each field represents a stage of the pipeline:
    - Input: user goal + target
    - Planner output: the plan
    - Execution output: tool results
    - Analysis output: correlated findings
    - Report output: final report
    """

    # --- Input ---
    scan_id: str
    target: str
    objective: str

    # --- Status ---
    status: str                         # Current scan status
    error: str                          # Error message if something fails

    # --- Planner Output ---
    plan: dict                          # ReconPlan as dict

    # --- Execution Output ---
    tool_results: list[dict]            # List of ToolResult as dicts

    # --- RAG Context ---
    rag_context: str                    # Retrieved security context

    # --- Analysis Output ---
    analysis: dict                      # AnalysisResult as dict

    # --- Report Output ---
    report: dict                        # ReconReport as dict
    
    # --- Internal ---
    _progress_callback: Annotated[Any, "internal progress callback"] | None
