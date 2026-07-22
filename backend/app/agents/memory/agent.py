"""
Memory Agent — persists structured market intelligence from the event bus.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.agents.base import BaseAgent
from app.agents.memory.retrieval import MemoryRetrieval
from app.agents.memory.storage import MemoryStorage
from app.core.logger import get_logger
from app.core.settings import settings
from app.events.base import Event
from app.events.types import EventType
from app.memory.service import MemoryService

logger = get_logger("athena.agents.memory")


class MemoryAgent(BaseAgent):
    id = "memory"
    name = "Memory Agent"
    version = "1.0.0"
    priority = 55
    subscribed_events = [
        EventType.TECHNICAL_ANALYSIS_COMPLETED,
        EventType.SMC_ANALYSIS_COMPLETED,
        EventType.RISK_ASSESSMENT_COMPLETED,
        EventType.TRADE_VALIDATION_COMPLETED,
        EventType.NEWS_ANALYSIS_COMPLETED,
        EventType.REASONING_COMPLETED,
        EventType.TRADE_CLOSED,
        EventType.LEARNING_COMPLETED,
        EventType.PORTFOLIO_UPDATED,
        EventType.WATCHLIST_OPPORTUNITY_DETECTED,
        EventType.NOTIFICATION_DISPATCHED,
    ]

    def __init__(self) -> None:
        super().__init__()
        self._storage = MemoryStorage(MemoryService())
        self._retrieval = MemoryRetrieval(MemoryService())
        self._stored = 0

    @property
    def retrieval(self) -> MemoryRetrieval:
        return self._retrieval

    async def handle_event(self, event: Event) -> None:
        if not settings.MEMORY_AGENT_ENABLED:
            return

        payload = dict(event.payload or {})
        correlation_id = event.correlation_id or payload.get("correlation_id")

        record = await asyncio.to_thread(
            self._storage.store_from_event_type,
            str(event.type),
            payload,
            correlation_id=str(correlation_id) if correlation_id else None,
        )
        if record is not None:
            self._stored += 1
            logger.info(
                "agent=%s action=store id=%s type=%s status=ok",
                self.id,
                record.id,
                record.memory_type,
            )

    def health(self) -> dict[str, Any]:
        base = super().health()
        base.update({"memories_stored": self._stored})
        return base
