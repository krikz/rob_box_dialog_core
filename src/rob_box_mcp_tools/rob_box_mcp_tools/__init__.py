"""rob_box_mcp_tools в ядре (ADR-0167 §2.1) — НЕПОЛНЫЙ пакет без ROS.

В pip-ядро входит только ROS-free часть: base, owner_event, voice_request и тул
search_web (tools/web_search.py, перенесён в Ш3). Полный пакет (navigation, system,
memory, music, …) живёт у робота — ставить это ядро в одно окружение с полным пакетом
робота нельзя (комментарий в pyproject.toml).
"""

from rob_box_mcp_tools.base import (  # noqa: F401
    MCPTool,
    MCPToolParameter,
    MCPToolResult,
    ToolExecutionType,
)

__version__ = "0.7.2"
