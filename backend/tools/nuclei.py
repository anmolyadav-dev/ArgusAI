"""
Nuclei wrapper — Vulnerability scanning using templates.
"""

from backend.tools.base import BaseTool
from backend.schemas import ToolResult


class NucleiTool(BaseTool):
    name = "nuclei"
    category = "vulnerability"
    binary = "nuclei"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Run nuclei with default templates against a target.
        Scans for known vulnerabilities, misconfigurations, and exposures.
        """
        severity = kwargs.get("severity", "critical,high,medium")

        command = [
            self.binary,
            "-u", target,
            "-silent",
            "-severity", severity,   # Filter by severity
            "-json",                 # JSON output for parsing
            "-timeout", "10",        # Per-request timeout
            "-rate-limit", "50",     # Be respectful
        ]

        stdout, stderr, code = await self.execute_command(command, timeout=600)

        # Parse JSON output — each line is a JSON object
        results = [
            line.strip()
            for line in stdout.splitlines()
            if line.strip()
        ]

        return ToolResult(
            tool=self.name,
            category=self.category,
            target=target,
            results=results,
            raw_output=stdout,
            error=stderr if code != 0 else None,
        )
