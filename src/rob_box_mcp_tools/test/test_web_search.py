"""Unit-тесты rob_box_mcp_tools.tools.web_search (поиск колонки, перенесён в ядро, ADR-0167 Ш3).

Без сети и без ROS: ddgs подменяется заглушкой (пакета нет), DeepSeek — транспортом.
Покрываем контракт, который использует хост колонки (SearchWebTool + transport=):
ddgs → DeepSeek фолбэк, честное «0 результатов», отказ search_unavailable, и локальный
urllib-транспорт (в ядре нет клиента KIE).
"""

from __future__ import annotations

from types import SimpleNamespace

from rob_box_mcp_tools.tools.web_search import (
    SEARCH_UNAVAILABLE,
    SearchWebTool,
    _urllib_transport,
)


def _log():
    return SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)


def _node():
    return SimpleNamespace(get_logger=lambda: _log())


def _tool(transport=None, environ=None, ddgs_available=False, ddgs_rows=None):
    tool = SearchWebTool(_node(), transport=transport, environ=environ or {"DEEPSEEK_API_KEY": "sk-test"})
    tool._ddgs_available = ddgs_available
    if ddgs_available:
        tool._ddgs_cls = object
        tool._ddgs_text = lambda *_a, **k: ddgs_rows if ddgs_rows is not None else []
    return tool


def test_deepseek_answers_when_ddgs_absent():
    import json

    seen = {}

    def transport(method, url, headers, body, timeout):
        seen["url"] = url
        assert json.loads(body)["query"] == "погода"
        return 200, json.dumps({"results": [{"title": "t", "summary": "s", "url": "u"}]}).encode()

    tool = _tool(transport=transport)
    res = tool.execute("погода", max_results=1)
    assert res.success
    assert res.data["backend"] == "deepseek"
    assert res.data["results"][0]["body"] == "s"


def test_empty_deepseek_is_honest_zero_results():
    import json

    def transport(method, url, headers, body, timeout):
        return 200, json.dumps({"results": []}).encode()

    tool = _tool(transport=transport)
    res = tool.execute("танец утят", max_results=1)
    assert res.success
    assert res.data["results"] == []
    assert res.data["backend"] == "deepseek"


def test_all_backends_down_is_search_unavailable():
    tool = _tool(transport=None, environ={})
    res = tool.execute("погода", max_results=1)
    assert not res.success
    assert res.data["reason"] == SEARCH_UNAVAILABLE
    assert res.data["status"] == "rejected"


def test_ddgs_answers_first():
    tool = _tool(environ={}, ddgs_available=True, ddgs_rows=[{"title": "t", "body": "b", "href": "h"}])
    res = tool.execute("погода", max_results=1)
    assert res.success
    assert res.data["backend"] == "ddgs"
    assert res.data["results"][0]["body"] == "b"


def test_empty_query_rejected():
    tool = _tool(environ={})
    res = tool.execute("   ")
    assert not res.success
    assert res.error == "empty_query"


def test_tool_metadata():
    tool = SearchWebTool(_node(), environ={})
    assert tool.name == "search_web"
    assert not tool.destructive
    params = {p.name for p in tool.parameters}
    assert {"query", "max_results"} <= params


def test_urllib_transport_is_callable():
    assert callable(_urllib_transport)
