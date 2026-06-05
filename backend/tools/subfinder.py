"""
Subfinder wrapper — Fast passive subdomain enumeration.
"""

from backend.tools.base import BaseTool
from backend.schemas import ToolResult


class SubfinderTool(BaseTool):
    name = "subfinder"
    category = "subdomain"
    binary = "subfinder"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Run subfinder to discover subdomains passively.
        Uses public sources like crt.sh, VirusTotal, etc.
        """
        command = [
            self.binary,
            "-d", target,        # Target domain
            "-silent",           # Only output subdomains
            "-timeout", "30",    # Timeout per source
        ]

        stdout, stderr, code = await self.execute_command(command)

        # Parse output — subfinder outputs one subdomain per line
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
