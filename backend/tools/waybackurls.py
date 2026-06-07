"""
Waybackurls wrapper — Fetch historical URLs from the Wayback Machine.
"""

from backend.tools.base import BaseTool
from backend.schemas import ToolResult


class WaybackurlsTool(BaseTool):
    name = "waybackurls"
    category = "url"
    binary = "waybackurls"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Fetch URLs from the Wayback Machine for a domain.
        Discovers endpoints that may no longer be linked but still accessible.
        """
        command = [self.binary, target]

        stdout, stderr, code = await self.execute_command(command, timeout=120)

        urls = [
            line.strip()
            for line in stdout.splitlines()
            if line.strip() and "http" in line
        ]

        return ToolResult(
            tool=self.name,
            category=self.category,
            target=target,
            results=urls,
            raw_output=stdout,
            error=stderr if code != 0 else None,
        )
