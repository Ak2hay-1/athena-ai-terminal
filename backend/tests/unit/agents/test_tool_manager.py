"""Unit tests for ToolManager."""

from __future__ import annotations

from typing import Any

import pytest

from app.tools.base import BaseTool
from app.tools.manager import ToolManager
from app.tools.manager import ToolNotFoundError
from app.tools.stubs import MarketDataTool
from app.tools.stubs import create_default_tools


class _EchoTool(BaseTool):
    id = "echo"
    name = "Echo Tool"

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        return {"status": "ok", "echo": kwargs}


@pytest.mark.asyncio
async def test_register_get_list_execute() -> None:
    manager = ToolManager()
    tool = _EchoTool()
    manager.register(tool)

    assert manager.get("echo") is tool
    assert len(manager.list()) == 1

    result = await manager.execute("echo", value=42)
    assert result == {"status": "ok", "echo": {"value": 42}}


@pytest.mark.asyncio
async def test_unknown_tool_raises() -> None:
    manager = ToolManager()
    with pytest.raises(ToolNotFoundError):
        manager.get("missing")

    with pytest.raises(ToolNotFoundError):
        await manager.execute("missing")


@pytest.mark.asyncio
async def test_default_stub_tools() -> None:
    manager = ToolManager()
    for tool in create_default_tools():
        manager.register(tool)

    ids = {tool.id for tool in manager.list()}
    assert ids == {
        "market_data",
        "news",
        "database",
        "recommendation",
        "notification",
        "memory",
    }

    market = MarketDataTool()
    assert market.id == "market_data"
    assert market.name == "Market Data Tool"
