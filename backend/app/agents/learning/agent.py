"""
Pattern Intelligence (Learning) Agent.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from app.agents.base import BaseAgent
from app.agents.learning.analyzer import analyze_patterns
from app.core.logger import get_logger
from app.core.settings import settings
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType
from app.memory.service import MemoryService

logger = get_logger("athena.agents.learning")


class LearningAgent(BaseAgent):
    id = "learning"
    name = "Learning Agent"
    version = "1.0.0"
    priority = 60
    subscribed_events = [EventType.TRADE_CLOSED, EventType.SYSTEM_TICK]

    def __init__(self) -> None:
        super().__init__()
        self._last_scan_mono = 0.0
        self._runs = 0

    async def handle_event(self, event: Event) -> None:
        if not settings.LEARNING_AGENT_ENABLED:
            return

        event_type = str(event.type)
        if event_type == EventType.SYSTEM_TICK:
            interval = max(60, int(settings.LEARNING_SCAN_INTERVAL_SECONDS))
            now = time.monotonic()
            if self._last_scan_mono and (now - self._last_scan_mono) < interval:
                return
        elif event_type != EventType.TRADE_CLOSED:
            return

        started = time.perf_counter()
        report = await asyncio.to_thread(analyze_patterns)

        # Persist statistic snapshot
        await asyncio.to_thread(
            MemoryService().store,
            agent_id="learning",
            memory_type="statistic",
            payload=report,
            notes="learning_completed",
        )

        self._last_scan_mono = time.monotonic()
        self._runs += 1
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "agent=%s action=analyze status=ok sample_size=%s win_rate=%s "
            "duration_ms=%.2f",
            self.id,
            report.get("sample_size"),
            report.get("win_rate"),
            duration_ms,
        )

        publisher = self._publisher or EventPublisher()
        await publisher.publish(
            EventType.LEARNING_COMPLETED,
            source=self.id,
            payload=report,
            correlation_id=event.correlation_id,
        )

    def health(self) -> dict[str, Any]:
        base = super().health()
        base.update({"learning_runs": self._runs})
        return base
