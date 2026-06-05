"""
Tool registry — Maps tool names to their wrapper classes.
This is the single source of truth for available tools.
"""

from backend.tools.subfinder import SubfinderTool
from backend.tools.assetfinder import AssetfinderTool
from backend.tools.sublist3r import Sublist3rTool
from backend.tools.httpx_tool import HttpxTool, HttpxProbeTool
from backend.tools.nuclei import NucleiTool
from backend.tools.dnsx import DnsxTool
from backend.tools.ffuf import FfufTool
from backend.tools.katana import KatanaTool
from backend.tools.waybackurls import WaybackurlsTool
from backend.tools.gospider import GospiderTool
from backend.tools.cloud_enum import CloudEnumTool
from backend.tools.base import BaseTool


# ============================================================
# Tool Registry
# Maps tool names (as used by the Planner) to wrapper instances.
# ============================================================

TOOL_REGISTRY: dict[str, BaseTool] = {
    "subfinder": SubfinderTool(),
    "assetfinder": AssetfinderTool(),
    "sublist3r": Sublist3rTool(),
    "httpx": HttpxTool(),
    "httpx_probe": HttpxProbeTool(),
    "nuclei": NucleiTool(),
    "dnsx": DnsxTool(),
    "ffuf": FfufTool(),
    "katana": KatanaTool(),
    "waybackurls": WaybackurlsTool(),
    "gospider": GospiderTool(),
    "cloud_enum": CloudEnumTool(),
}


def get_tool(name: str) -> BaseTool | None:
    """Look up a tool by name."""
    return TOOL_REGISTRY.get(name)


def get_available_tools() -> list[str]:
    """Return names of tools that are actually installed on this system."""
    return [
        name for name, tool in TOOL_REGISTRY.items()
        if tool.is_available()
    ]


def get_all_tool_names() -> list[str]:
    """Return all registered tool names."""
    return list(TOOL_REGISTRY.keys())
