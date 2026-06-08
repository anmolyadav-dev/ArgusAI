"""
GoSpider wrapper — Web spidering and link extraction.
"""

from backend.tools.base import BaseTool
from backend.schemas import ToolResult


class GospiderTool(BaseTool):
    name = "gospider"
    category = "url"
    binary = "gospider"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Run gospider to crawl websites and extract URLs.
        Discovers links, forms, and JavaScript files.
        """
        if not target.startswith("http"):
            target = f"https://{target}"

        command = [
            self.binary,
            "-s", target,
            "-d", "2",           # Crawl depth
            "-t", "5",           # Threads
            "--no-redirect",
            "-q",                # Quiet mode
        ]

        stdout, stderr, code = await self.execute_command(command, timeout=180)

        # GoSpider prefixes lines with tags like [url], [href], etc.
        urls = []
        for line in stdout.splitlines():
            line = line.strip()
            if line and ("http" in line):
                # Extract URL from tagged output
                parts = line.split(" - ", 1)
                url = parts[-1].strip() if len(parts) > 1 else line
                if url.startswith("http"):
                    urls.append(url)

        return ToolResult(
            tool=self.name,
            category=self.category,
            target=target,
            results=urls,
            raw_output=stdout,
            error=stderr if code != 0 else None,
        )
