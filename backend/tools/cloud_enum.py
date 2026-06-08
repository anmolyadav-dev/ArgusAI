"""
Cloud Enum wrapper — Cloud infrastructure enumeration.
"""

from backend.tools.base import BaseTool
from backend.schemas import ToolResult


class CloudEnumTool(BaseTool):
    name = "cloud_enum"
    category = "cloud"
    binary = "cloud_enum"

    async def run(self, target: str, **kwargs) -> ToolResult:
        """
        Enumerate cloud resources (S3 buckets, Azure blobs, GCP buckets).
        Searches for publicly accessible cloud storage related to target.
        """
        command = [
            self.binary,
            "-k", target,     # Keyword (domain name)
        ]

        stdout, stderr, code = await self.execute_command(command, timeout=300)

        results = [
            line.strip()
            for line in stdout.splitlines()
            if line.strip() and not line.startswith("[")
        ]

        return ToolResult(
            tool=self.name,
            category=self.category,
            target=target,
            results=results,
            raw_output=stdout,
            error=stderr if code != 0 else None,
        )
