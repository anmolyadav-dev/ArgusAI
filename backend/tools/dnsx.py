"""
DNSX wrapper — DNS enumeration and resolution.
"""

from backend.tools.base import BaseTool
from backend.schemas import ToolResult


class DnsxTool(BaseTool):
    name = "dnsx"
    category = "dns"
    binary = "dnsx"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Run dnsx to resolve DNS records for a domain.
        Performs A, AAAA, CNAME, MX, NS, TXT, and SOA lookups.
        """
        command = [
            self.binary,
            "-d", target,
            "-silent",
            "-a",           # A records
            "-aaaa",        # AAAA records
            "-cname",       # CNAME records
            "-mx",          # MX records
            "-ns",          # NS records
            "-txt",         # TXT records
            "-resp",        # Show response
        ]

        stdout, stderr, code = await self.execute_command(command)

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
