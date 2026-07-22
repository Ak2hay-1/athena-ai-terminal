"""
Watchlist Intelligence Agent.
"""

from __future__ import annotations

import time
from typing import Any

from app.agents.base import BaseAgent
from app.agents.watchlist.detector import is_opportunity
from app.agents.watchlist.detector import opportunity_payload
from app.agents.watchlist.filter import filter_payload_for_users
from app.agents.watchlist.preferences import load_watch_contexts
from app.core.logger import get_logger
from app.core.settings import settings
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType

logger = get_logger("athena.agents.watchlist")


class WatchlistAgent(BaseAgent):
    id = "watchlist"
    name = "Watchlist Agent"
    version = "1.0.0"
    priority = 75
    subscribed_events = [
        EventType.TRADE_VALIDATION_COMPLETED,
        EventType.TECHNICAL_ANALYSIS_COMPLETED,
    ]

    def __init__(self) -> None:
        super().__init__()
        self._dedupe: dict[str, float] = {}
        self._published = 0

    async def handle_event(self, event: Event) -> None:
        if not settings.WATCHLIST_AGENT_ENABLED:
            return
        et = str(event.type)
        payload = dict(event.payload or {})
        if not is_opportunity(payload, event_type=et):
            return

        contexts = load_watch_contexts()
        matched = filter_payload_for_users(contexts, payload)
        if not matched:
            return

        publisher = self._publisher or EventPublisher()
        ttl = max(30, int(settings.WATCHLIST_DEDUP_TTL_SECONDS))
        now = time.monotonic()

        for ctx in matched:
            key = f"{ctx.user_id}:{payload.get('symbol')}:{payload.get('timeframe')}"
            last = self._dedupe.get(key, 0.0)
            if now - last < ttl:
                continue
            self._dedupe[key] = now
            opp = opportunity_payload(payload, user_id=ctx.user_id, event_type=et)
            await publisher.publish(
                EventType.WATCHLIST_OPPORTUNITY_DETECTED,
                source=self.id,
                payload=opp,
                correlation_id=event.correlation_id or key,
            )
            self._published += 1
            logger.info(
                "agent=%s action=opportunity user_id=%s symbol=%s confluence=%s",
                self.id,
                ctx.user_id,
                opp.get("symbol"),
                opp.get("confluence"),
            )

        # prune dedupe map
        if len(self._dedupe) > 2000:
            cutoff = now - ttl
            self._dedupe = {k: v for k, v in self._dedupe.items() if v >= cutoff}

    def health(self) -> dict[str, Any]:
        return {
            "enabled": settings.WATCHLIST_AGENT_ENABLED,
            "published": self._published,
        }
