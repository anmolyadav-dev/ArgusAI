"""
Base class for all recon tool wrappers.
Every tool wrapper inherits from this and implements the `run` method.
"""

import asyncio
import time
import shutil
from abc import ABC, abstractmethod

from backend.schemas import ToolResult
from backend.config import settings


class BaseTool(ABC):
    """
    Base class for recon tool wrappers.
    
    Each tool wrapper:
    1. Defines its name and category
    2. Implements `run(target)` to execute the tool
    3. Returns a normalized ToolResult
    
    Tools are executed as async subprocesses with timeouts.
    """

    # Subclasses must set these
    name: str = ""
    category: str = ""  # subdomain, dns, live_host, url, vuln, tech, etc.
    binary: str = ""    # Name of the binary to execute

    def is_available(self) -> bool:
        """Check if the tool binary is installed on the system."""
        return shutil.which(self.binary) is not None

    async def execute_command(self, command: list[str], timeout: int | None = None) -> tuple[str, str, int]:
        """
        Run a shell command asynchronously.
        
        Args:
            command: Command and arguments as a list
            timeout: Maximum seconds to wait (defaults to settings.tool_timeout)
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        timeout = timeout or settings.tool_timeout

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            return (
                stdout.decode("utf-8", errors="replace").strip(),
                stderr.decode("utf-8", errors="replace").strip(),
                process.returncode or 0,
            )

        except asyncio.TimeoutError:
            # Kill the process if it takes too long
            try:
                process.kill()
            except ProcessLookupError:
                pass
            return "", f"Tool {self.name} timed out after {timeout}s", -1

        except FileNotFoundError:
            return "", f"Tool binary '{self.binary}' not found", -1

    @abstractmethod
    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Execute the tool against a target and return normalized results.
        
        Args:
            target: Domain, IP, or URL to scan
            
        Returns:
            ToolResult with normalized output
        """
        pass

    async def safe_run(self, target: str, **kwargs) -> ToolResult:
        """
        Run the tool with error handling and timing.
        This is the method called by the execution engine.
        """
        start_time = time.time()

        # Check if tool is available
        if not self.is_available():
            return ToolResult(
                tool=self.name,
                category=self.category,
                target=target,
                error=f"{self.binary} is not installed or not in PATH",
                execution_time=0.0,
            )

        try:
            result = await self.run(target, **kwargs)
            result.execution_time = round(time.time() - start_time, 2)
            return result

        except Exception as e:
            return ToolResult(
                tool=self.name,
                category=self.category,
                target=target,
                error=str(e),
                execution_time=round(time.time() - start_time, 2),
            )
