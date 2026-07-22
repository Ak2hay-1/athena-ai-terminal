"""
News Intelligence Agent — collect, classify, publish NewsAnalysisCompleted.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from datetime import timezone
from typing import Any

from app.agents.base import BaseAgent
from app.agents.news.classifier import classify_items
from app.agents.news.collector import collect_news
from app.agents.news.impact import enrich_impact
from app.core.logger import get_logger
from app.core.settings import settings
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType

logger = get_logger("athena.agents.news")


class NewsAgent(BaseAgent):
    id = "news"
    name = "News Agent"
    version = "1.0.0"
    priority = 90
    subscribed_events = [EventType.SYSTEM_TICK]

    def __init__(self) -> None:
        super().__init__()
        self._last_scan_mono = 0.0
        self._analyses = 0

    async def handle_event(self, event: Event) -> None:
        if not settings.NEWS_AGENT_ENABLED:
            return
        if str(event.type) != EventType.SYSTEM_TICK:
            return

        interval = max(60, int(settings.NEWS_AGENT_SCAN_INTERVAL_SECONDS))
        now = time.monotonic()
        if self._last_scan_mono and (now - self._last_scan_mono) < interval:
            return

        started = time.perf_counter()
        raw_items = await asyncio.to_thread(collect_news, sync=True, limit=40)
        classified = await asyncio.to_thread(classify_items, raw_items)
        items = await asyncio.to_thread(enrich_impact, classified)

        bullish = sum(1 for i in items if i.get("sentiment_code") == "BULLISH")
        bearish = sum(1 for i in items if i.get("sentiment_code") == "BEARISH")
        neutral = sum(1 for i in items if i.get("sentiment_code") == "NEUTRAL")
        high_impact = sum(1 for i in items if i.get("impact") == "High")

        payload = {
            "items": [
                {
                    "headline": i.get("title"),
                    "sentiment": i.get("sentiment"),
                    "impact": i.get("impact"),
                    "symbols": i.get("symbols"),
                    "currencies": i.get("currencies"),
                    "source": i.get("source"),
                    "published_at": i.get("published_at"),
                }
                for i in items
            ],
            "summary": {
                "total": len(items),
                "bullish": bullish,
                "bearish": bearish,
                "neutral": neutral,
                "high_impact": high_impact,
            },
            "as_of": datetime.now(timezone.utc).isoformat(),
        }

        self._last_scan_mono = time.monotonic()
        self._analyses += 1
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "agent=%s action=analyze status=ok items=%s duration_ms=%.2f",
            self.id,
            len(items),
            duration_ms,
        )

        publisher = self._publisher or EventPublisher()
        await publisher.publish(
            EventType.NEWS_ANALYSIS_COMPLETED,
            source=self.id,
            payload=payload,
        )

    def health(self) -> dict[str, Any]:
        base = super().health()
        base.update({"analyses_completed": self._analyses})
        return base
