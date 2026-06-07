"""
FFUF wrapper — Directory and file enumeration via fuzzing.
"""

from backend.tools.base import BaseTool
from backend.schemas import ToolResult


class FfufTool(BaseTool):
    name = "ffuf"
    category = "directory"
    binary = "ffuf"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Run ffuf to discover hidden directories and files.
        Uses a wordlist to fuzz URL paths.
        """
        wordlist = kwargs.get(
            "wordlist",
            "/usr/share/wordlists/dirb/common.txt"
        )

        # Ensure target has a scheme
        if not target.startswith("http"):
            target = f"https://{target}"

        command = [
            self.binary,
            "-u", f"{target}/FUZZ",   # FUZZ placeholder in URL
            "-w", wordlist,           # Wordlist path
            "-mc", "200,301,302,403", # Match these status codes
            "-t", "20",               # Number of threads
            "-timeout", "10",         # Request timeout
            "-s",                     # Silent mode
        ]

        stdout, stderr, code = await self.execute_command(command, timeout=300)

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
