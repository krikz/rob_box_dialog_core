"""Тулы ядра (ADR-0167 Ш3): только ROS-free search_web.

НЕ копия полного tools/ робота (тогда инициализация тянула бы navigation/memory/music).
Хост колонки грузит тул тем же путём, что раньше: dry_stand.load_tool_module("web_search")
(только теперь из поставленного пакета, а не из чекаута src/).
"""

from rob_box_mcp_tools.tools.web_search import SearchWebTool  # noqa: F401

__all__ = ["SearchWebTool"]
