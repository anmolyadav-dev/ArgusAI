"""
Assetfinder wrapper — Find related domains and subdomains.
"""

from backend.tools.base import BaseTool
from backend.schemas import ToolResult


class AssetfinderTool(BaseTool):
    name = "assetfinder"
    category = "subdomain"
    binary = "assetfinder"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Run assetfinder to find domains associated with a target.
        Uses certificate transparency logs and other sources.
        """
        command = [
            self.binary,
            "--subs-only",  # Only return subdomains
            target,
        ]

        stdout, stderr, code = await self.execute_command(command)

        # Parse — one domain per line
        subdomains = [
            line.strip()
            for line in stdout.splitlines()
            if line.strip() and "." in line
        ]

        return ToolResult(
            tool=self.name,
            category=self.category,
            target=target,
            results=subdomains,
            raw_output=stdout,
            error=stderr if code != 0 else None,
        )
