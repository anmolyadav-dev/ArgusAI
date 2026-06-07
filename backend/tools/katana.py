"""
Katana wrapper — Web crawling and spidering.
"""

from backend.tools.base import BaseTool
from backend.schemas import ToolResult


class KatanaTool(BaseTool):
    name = "katana"
    category = "url"
    binary = "katana"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Run katana to crawl a website and discover URLs.
        Follows links, parses JavaScript, and finds endpoints.
        """
        if not target.startswith("http"):
            target = f"https://{target}"

        command = [
            self.binary,
            "-u", target,
            "-silent",
            "-depth", "3",          # Crawl depth
            "-js-crawl",            # Also crawl JavaScript files
            "-known-files", "all",  # Check known files (robots.txt, etc.)
        ]

        stdout, stderr, code = await self.execute_command(command, timeout=300)

        urls = [
            line.strip()
            for line in stdout.splitlines()
            if line.strip() and ("http" in line or "/" in line)
        ]

        return ToolResult(
            tool=self.name,
            category=self.category,
            target=target,
            results=urls,
            raw_output=stdout,
            error=stderr if code != 0 else None,
        )
