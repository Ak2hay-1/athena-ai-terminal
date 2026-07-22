"""
Stub tool implementations (no trading / recommendation logic).
"""

from __future__ import annotations

from typing import Any

from app.tools.base import BaseTool
from app.tools.market_data_tool import MarketDataTool


class _StubTool(BaseTool):
    """Base for tools that are registered but not wired to domain services."""

    id: str = "stub"
    name: str = "Stub Tool"
    description: str = "Unwired stub tool"

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "status": "not_wired",
            "tool_id": self.id,
            "kwargs": kwargs,
        }


class NewsTool(_StubTool):
    id = "news"
    name = "News Tool"
    description = "Fetch news and sentiment (stub)"


class DatabaseTool(_StubTool):
    id = "database"
    name = "Database Tool"
    description = "Generic database access (stub)"


class RecommendationTool(_StubTool):
    id = "recommendation"
    name = "Recommendation Tool"
    description = "Read recommendations (stub — does not generate)"


class NotificationTool(BaseTool):
    id = "notification"
    name = "Notification Tool"
    description = "Dispatch multi-channel notifications"

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        from app.notifications.message import NotificationMessage
        from app.notifications.router import notification_router

        user_id = kwargs.get("user_id")
        if user_id is None:
            return {"status": "error", "error": "user_id required"}
        message = NotificationMessage(
            user_id=int(user_id),
            message_type=str(kwargs.get("message_type") or "Market Alert"),
            priority=str(kwargs.get("priority") or "Medium"),
            summary=str(kwargs.get("summary") or ""),
            confidence=kwargs.get("confidence"),
            reasoning=list(kwargs.get("reasoning") or []),
            risk=kwargs.get("risk"),
            stop_loss=kwargs.get("stop_loss"),
            take_profit=kwargs.get("take_profit"),
            evidence=list(kwargs.get("evidence") or []),
            action=kwargs.get("action"),
            symbol=kwargs.get("symbol"),
            side=kwargs.get("side"),
            dedupe_key=kwargs.get("dedupe_key"),
        )
        results = await notification_router.dispatch(message)
        return {"status": "ok", "results": results}


class MemoryTool(BaseTool):
    """
    Persists trading intelligence via MemoryService when available.
    """

    id = "memory"
    name = "Memory Tool"
    description = "Store and query agent trading memory"

    def __init__(self, memory_service: Any | None = None) -> None:
        self._memory = memory_service

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        action = str(kwargs.get("action", "store"))
        if self._memory is None:
            return {
                "status": "not_wired",
                "tool_id": self.id,
                "action": action,
            }

        if action == "store":
            record = self._memory.store(
                agent_id=str(kwargs.get("agent_id", "unknown")),
                memory_type=str(kwargs.get("memory_type", "observation")),
                payload=kwargs.get("payload") or {},
                symbol=kwargs.get("symbol"),
                timeframe=kwargs.get("timeframe"),
                correlation_id=kwargs.get("correlation_id"),
                meta=kwargs.get("meta"),
            )
            return {
                "status": "ok",
                "tool_id": self.id,
                "action": action,
                "id": getattr(record, "id", None),
            }

        if action == "query":
            rows = self._memory.query(
                agent_id=kwargs.get("agent_id"),
                memory_type=kwargs.get("memory_type"),
                symbol=kwargs.get("symbol"),
                limit=int(kwargs.get("limit", 50)),
            )
            return {
                "status": "ok",
                "tool_id": self.id,
                "action": action,
                "count": len(rows),
                "items": [row.to_dict() for row in rows],
            }

        if action == "stats":
            return {
                "status": "ok",
                "tool_id": self.id,
                "action": action,
                "stats": self._memory.stats(agent_id=kwargs.get("agent_id")),
            }

        return {
            "status": "error",
            "tool_id": self.id,
            "error": f"unknown_action:{action}",
        }


def create_default_tools(memory_service: Any | None = None) -> list[BaseTool]:
    """Factory for the standard stub tool set."""
    return [
        MarketDataTool(),
        NewsTool(),
        DatabaseTool(),
        RecommendationTool(),
        NotificationTool(),
        MemoryTool(memory_service=memory_service),
    ]
