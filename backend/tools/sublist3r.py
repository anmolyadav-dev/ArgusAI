"""
Sublist3r wrapper — Subdomain enumeration using multiple search engines.
"""

from backend.tools.base import BaseTool
from backend.schemas import ToolResult


class Sublist3rTool(BaseTool):
    name = "sublist3r"
    category = "subdomain"
    binary = "sublist3r"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Run Sublist3r to enumerate subdomains using search engines.
        Uses Google, Yahoo, Bing, Baidu, and more.
        """
        command = [
            self.binary,
            "-d", target,  # Target domain
            "-n",          # No bruteforce, just passive
        ]

        stdout, stderr, code = await self.execute_command(command)

        # Sublist3r outputs subdomains mixed with status messages
        # Filter to only lines that look like domains
        subdomains = []
        for line in stdout.splitlines():
            line = line.strip()
            if line and "." in line and " " not in line and target in line:
                subdomains.append(line)

        return ToolResult(
            tool=self.name,
            category=self.category,
            target=target,
            results=subdomains,
            raw_output=stdout,
            error=stderr if code != 0 else None,
        )
