"""
Execution Engine — Pure Python, no AI.
Reads the Planner's JSON plan and executes tools concurrently.
Streams progress updates and collects normalized results.
"""

import asyncio
from typing import Callable
import logging

from backend.schemas import ReconPlan, ToolResult, ProgressUpdate, ScanStatus
from backend.tools import get_tool, get_available_tools


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ExecutionEngine:
    """
    Executes recon tools according to a plan.
    
    This is NOT an AI agent. It's straightforward Python:
    1. Read the plan stages
    2. For each stage, run the specified tools
    3. Tools within the same stage run concurrently
    4. Collect and return all results
    """

    def __init__(self, progress_callback: Callable | None = None):
        """
        Args:
            progress_callback: Optional async function called with ProgressUpdate
                              for real-time streaming to the frontend.
        """
        self.progress_callback = progress_callback
        self.results: list[ToolResult] = []

    async def _notify(self, scan_id: str, stage: str, tool: str,
                      message: str, progress: int):
        """Send a progress update if a callback is registered."""
        if self.progress_callback:
            update = ProgressUpdate(
                scan_id=scan_id,
                status=ScanStatus.EXECUTING,
                stage=stage,
                tool=tool,
                message=message,
                progress_percent=progress,
            )
            await self.progress_callback(update)

    async def _run_tool(self, tool_name: str, target: str,
                        scan_id: str, stage: str, **kwargs) -> ToolResult:
        """Run a single tool and handle errors."""
        tool = get_tool(tool_name)

        if tool is None:
            return ToolResult(
                tool=tool_name,
                category="unknown",
                target=target,
                error=f"Tool '{tool_name}' not found in registry",
            )

        await self._notify(scan_id, stage, tool_name,
                           f"Starting {tool_name}...", 0)
        logger.info(f"[Scan {scan_id}] Executing tool: {tool_name} on {target}")

        result = await tool.safe_run(target, **kwargs)

        # Report results
        if result.error:
            logger.error(f"[Scan {scan_id}] Tool {tool_name} failed: {result.error}")
            await self._notify(scan_id, stage, tool_name,
                               f"{tool_name} failed: {result.error}", 0)
        else:
            count = len(result.results)
            logger.info(f"Tool {tool_name} completed.")
            await self._notify(scan_id, stage, tool_name,
                               f"{tool_name} found {count} results", 0)

        return result

    async def execute(self, plan: ReconPlan, scan_id: str) -> list[ToolResult]:
        """
        Execute the full recon plan.
        
        Stages run sequentially (some stages depend on previous results).
        Tools within each stage run concurrently.
        
        Args:
            plan: The structured plan from the Planner Agent
            scan_id: Unique scan ID for tracking
            
        Returns:
            List of all ToolResult objects from every tool
        """
        self.results = []
        available = get_available_tools()
        total_stages = len(plan.plan)

        for stage_idx, stage in enumerate(plan.plan):
            stage_name = stage.stage.value
            progress_base = int((stage_idx / total_stages) * 100)

            await self._notify(
                scan_id, stage_name, "",
                f"Starting stage: {stage_name}",
                progress_base,
            )

            # Filter to only tools that are actually available
            tools_to_run = []
            for tool_name in stage.tools:
                if tool_name in available:
                    tools_to_run.append(tool_name)
                else:
                    await self._notify(
                        scan_id, stage_name, tool_name,
                        f"Skipping {tool_name} (not installed)",
                        progress_base,
                    )

            # Determine kwargs based on stage type
            kwargs = {}
            if stage_name == "technology_detection":
                kwargs["mode"] = "tech"

            # Run all tools in this stage concurrently
            if tools_to_run:
                tasks = [
                    self._run_tool(
                        tool_name, plan.target, scan_id, stage_name, **kwargs
                    )
                    for tool_name in tools_to_run
                ]
                stage_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Collect results, handling any exceptions
                for result in stage_results:
                    if isinstance(result, Exception):
                        self.results.append(ToolResult(
                            tool="unknown",
                            category=stage_name,
                            target=plan.target,
                            error=str(result),
                        ))
                    else:
                        self.results.append(result)

            stage_progress = int(((stage_idx + 1) / total_stages) * 100)
            await self._notify(
                scan_id, stage_name, "",
                f"Completed stage: {stage_name}",
                stage_progress,
            )

        await self._notify(
            scan_id, "complete", "",
            "All stages completed",
            100,
        )

        return self.results
