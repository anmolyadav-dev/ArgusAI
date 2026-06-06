"""
HTTPX wrapper — HTTP probing and technology detection.
Used for both live host detection and technology fingerprinting.
"""

from backend.tools.base import BaseTool
from backend.schemas import ToolResult


class HttpxTool(BaseTool):
    name = "httpx"
    category = "live_host"
    binary = "httpx"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Run httpx to probe HTTP services.
        
        Can be used in two modes:
        1. Live host detection: probe a list of subdomains
        2. Technology detection: fingerprint web technologies
        
        The mode depends on kwargs or how it's called.
        """
        # Determine the mode based on category override
        mode = kwargs.get("mode", "probe")

        if mode == "tech":
            # Technology detection mode
            self.category = "technology"
            command = [
                self.binary,
                "-u", target,
                "-silent",
                "-tech-detect",          # Detect technologies
                "-status-code",          # Show status codes
                "-title",                # Show page titles
                "-server",               # Show server header
                "-content-length",       # Show content length
                "-json",                 # JSON output
            ]
        else:
            # Default: live host probing
            command = [
                self.binary,
                "-u", target,
                "-silent",
                "-status-code",
                "-title",
                "-follow-redirects",
            ]

        stdout, stderr, code = await self.execute_command(command)

        # Parse output — httpx outputs one result per line
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


class HttpxProbeTool(BaseTool):
    """
    Variant that takes a file of subdomains and probes them all.
    Used after subdomain enumeration to find live hosts.
    """
    name = "httpx"
    category = "live_host"
    binary = "httpx"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Probe a list of hosts from a file or stdin.
        target here is a path to a file containing hostnames.
        """
        input_file = kwargs.get("input_file")

        if input_file:
            command = [
                self.binary,
                "-l", input_file,     # Read targets from file
                "-silent",
                "-status-code",
                "-title",
                "-follow-redirects",
            ]
        else:
            command = [
                self.binary,
                "-u", target,
                "-silent",
                "-status-code",
                "-title",
                "-follow-redirects",
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
