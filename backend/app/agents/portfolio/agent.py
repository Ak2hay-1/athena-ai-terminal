"""
Portfolio Intelligence Agent.
"""

from __future__ import annotations

import time
from datetime import datetime
from datetime import timezone
from typing import Any

from app.agents.base import BaseAgent
from app.agents.portfolio.health import portfolio_health_score
from app.agents.portfolio.metrics import compute_metrics
from app.agents.portfolio.recommendations import build_recommendations
from app.core.logger import get_logger
from app.core.settings import settings
from app.database.database import SessionLocal
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType
from app.repositories.paper_position_repository import PaperPositionRepository
from app.repositories.preferences_repository import PreferencesRepository

logger = get_logger("athena.agents.portfolio")


class PortfolioAgent(BaseAgent):
    id = "portfolio"
    name = "Portfolio Agent"
    version = "1.0.0"
    priority = 80
    subscribed_events = [
        EventType.SYSTEM_TICK,
        EventType.TRADE_CLOSED,
        EventType.TRADE_CREATED,
    ]

    def __init__(self) -> None:
        super().__init__()
        self._last_scan = 0.0
        self._runs = 0

    async def handle_event(self, event: Event) -> None:
        if not settings.PORTFOLIO_AGENT_ENABLED:
            return

        et = str(event.type)
        if et == EventType.SYSTEM_TICK:
            interval = max(15, int(settings.PORTFOLIO_SCAN_INTERVAL_SECONDS))
            now = time.monotonic()
            if now - self._last_scan < interval:
                return
            self._last_scan = now
            await self._scan_all_users()
            return

        if et in {EventType.TRADE_CLOSED, EventType.TRADE_CREATED}:
            user_id = event.payload.get("user_id")
            if user_id is not None:
                await self._publish_for_user(int(user_id))

    async def _scan_all_users(self) -> None:
        db = SessionLocal()
        try:
            user_ids = set(PaperPositionRepository(db).distinct_user_ids())
            user_ids.update(PreferencesRepository(db).list_all_user_ids())
        finally:
            db.close()

        for user_id in sorted(user_ids):
            await self._publish_for_user(user_id)

    async def _publish_for_user(self, user_id: int) -> None:
        payload = await self._build_payload(user_id)
        if payload is None:
            return
        publisher = self._publisher or EventPublisher()
        await publisher.publish(
            EventType.PORTFOLIO_UPDATED,
            source=self.id,
            payload=payload,
            correlation_id=f"portfolio-{user_id}",
        )
        self._runs += 1
        logger.info(
            "agent=%s action=portfolio_updated user_id=%s health=%s",
            self.id,
            user_id,
            payload.get("health_score"),
        )

    async def _build_payload(self, user_id: int) -> dict[str, Any] | None:
        db = SessionLocal()
        try:
            rows = PaperPositionRepository(db).list_for_user(user_id)
            positions = []
            for row in rows:
                data = row.to_trade_dict()
                data["closed_at"] = (
                    row.closed_at.isoformat() if row.closed_at else None
                )
                positions.append(data)
        finally:
            db.close()

        if not positions:
            return None

        metrics = compute_metrics(
            positions,
            account_balance=float(settings.PORTFOLIO_ACCOUNT_BALANCE),
        )
        health = portfolio_health_score(metrics)
        tips = build_recommendations(metrics, health)
        return {
            "user_id": user_id,
            "metrics": metrics,
            "health_score": health,
            "recommendations": tips,
            "as_of": datetime.now(timezone.utc).isoformat(),
        }

    def health(self) -> dict[str, Any]:
        base = super().health() if hasattr(super(), "health") else {}
        return {
            **base,
            "enabled": settings.PORTFOLIO_AGENT_ENABLED,
            "runs": self._runs,
        }
