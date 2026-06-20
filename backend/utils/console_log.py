"""
Console Logger — Pretty-print helpers for the terminal.
Gives a clear, structured view of the AI pipeline flow.
"""

import logging

logger = logging.getLogger("argus")


def _banner(label: str, char: str = "=", width: int = 60) -> str:
    padding = max(0, width - len(label) - 2)
    left = padding // 2
    right = padding - left
    return f"\n{char * left} {label} {char * right}"


def log_human_message(message: str, scan_id: str = ""):
    prefix = f"[{scan_id}] " if scan_id else ""
    logger.info(_banner(f"👤 HUMAN MESSAGE  {prefix}"))
    logger.info(f"  {message[:500]}")
    logger.info("=" * 62)


def log_ai_message(message: str, scan_id: str = ""):
    prefix = f"[{scan_id}] " if scan_id else ""
    logger.info(_banner(f"🤖 AI MESSAGE  {prefix}"))
    # Truncate long responses to 500 chars for readability
    preview = message[:500] + ("..." if len(message) > 500 else "")
    for line in preview.splitlines():
        logger.info(f"  {line}")
    logger.info("=" * 62)


def log_tool_call(tool_name: str, target: str, scan_id: str = ""):
    prefix = f"[{scan_id}] " if scan_id else ""
    logger.info(_banner(f"🔧 TOOL CALL  {prefix}", char="-"))
    logger.info(f"  Tool   : {tool_name}")
    logger.info(f"  Target : {target}")
    logger.info("-" * 62)


def log_tool_response(tool_name: str, result_count: int, error: str = "", scan_id: str = ""):
    prefix = f"[{scan_id}] " if scan_id else ""
    logger.info(_banner(f"📦 TOOL RESPONSE  {prefix}", char="-"))
    if error:
        logger.info(f"  Tool   : {tool_name}  ❌ FAILED")
        logger.info(f"  Error  : {error[:200]}")
    else:
        logger.info(f"  Tool   : {tool_name}  ✅ OK")
        logger.info(f"  Results: {result_count} item(s) found")
    logger.info("-" * 62)


def log_ai_node(node_name: str, description: str):
    logger.info(_banner(f"🧠 AI NODE: {node_name.upper()}", char="*"))
    logger.info(f"  {description}")
    logger.info("*" * 62)
