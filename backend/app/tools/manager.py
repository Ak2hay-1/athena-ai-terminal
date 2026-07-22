"""
Tool manager — agents request tools instead of calling services.
"""

from __future__ import annotations

from typing import Any

from app.core.logger import get_logger
from app.tools.base import BaseTool

logger = get_logger("athena.tools")


class ToolNotFoundError(KeyError):
    """Raised when a requested tool id is not registered."""


class ToolManager:
    """
    Registry and execution facade for agent tools.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.id] = tool
        logger.info("tool_manager action=register tool_id=%s name=%s", tool.id, tool.name)

    def unregister(self, tool_id: str) -> None:
        if tool_id in self._tools:
            del self._tools[tool_id]
            logger.info("tool_manager action=unregister tool_id=%s", tool_id)

    def get(self, tool_id: str) -> BaseTool:
        tool = self._tools.get(tool_id)
        if tool is None:
            raise ToolNotFoundError(tool_id)
        return tool

    def list(self) -> list[BaseTool]:
        return list(self._tools.values())

    async def execute(self, tool_id: str, **kwargs: Any) -> dict[str, Any]:
        tool = self.get(tool_id)
        logger.info("tool_manager action=execute tool_id=%s", tool_id)
        try:
            result = await tool.execute(**kwargs)
            logger.info(
                "tool_manager action=execute tool_id=%s status=ok",
                tool_id,
            )
            return result
        except Exception:
            logger.exception(
                "tool_manager action=execute tool_id=%s status=error",
                tool_id,
            )
            raise

    def health(self) -> dict[str, Any]:
        return {
            "tool_count": len(self._tools),
            "tools": [tool.health() for tool in self._tools.values()],
        }


tool_manager = ToolManager()
