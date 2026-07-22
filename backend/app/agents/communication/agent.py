"""
Communication Intelligence Agent — notify users without spam.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.agents.communication.composer import compose_from_event
from app.agents.communication.summaries import due_summaries_for_user
from app.core.logger import get_logger
from app.core.settings import settings
from app.database.database import SessionLocal
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType
from app.notifications.router import notification_router
from app.personalization.engine import personalization_engine
from app.models.user import User
from app.repositories.preferences_repository import PreferencesRepository
from sqlalchemy import select

logger = get_logger("athena.agents.communication")


class CommunicationAgent(BaseAgent):
    id = "communication"
    name = "Communication Agent"
    version = "1.0.0"
    priority = 70
    subscribed_events = [
        EventType.TRADE_VALIDATION_COMPLETED,
        EventType.LEARNING_COMPLETED,
        EventType.NEWS_ANALYSIS_COMPLETED,
        EventType.PORTFOLIO_UPDATED,
        EventType.WATCHLIST_OPPORTUNITY_DETECTED,
        EventType.TRADE_CLOSED,
        EventType.SYSTEM_TICK,
    ]

    def __init__(self) -> None:
        super().__init__()
        self._summary_state: dict[int, dict[str, str]] = {}
        self._dispatched = 0
        self._skipped = 0

    async def handle_event(self, event: Event) -> None:
        if not settings.COMMUNICATION_AGENT_ENABLED:
            return

        et = str(event.type)
        if et == EventType.SYSTEM_TICK:
            await self._handle_summaries()
            return

        payload = dict(event.payload or {})
        user_ids = self._resolve_user_ids(et, payload)
        if not user_ids:
            return

        for user_id in user_ids:
            message = compose_from_event(et, payload, user_id=user_id)
            await self._dispatch(message, event)

    async def _handle_summaries(self) -> None:
        db = SessionLocal()
        try:
            user_ids = list(db.scalars(select(User.id).where(User.is_active.is_(True))).all())
            prefs_ids = PreferencesRepository(db).list_all_user_ids()
            for uid in prefs_ids:
                if uid not in user_ids:
                    user_ids.append(uid)
        finally:
            db.close()

        for user_id in user_ids:
            state = self._summary_state.setdefault(user_id, {})
            for message in due_summaries_for_user(user_id, last_sent=state):
                await self._dispatch(message, None)

    async def _dispatch(self, message, event: Event | None) -> None:
        if not personalization_engine.should_notify(message.user_id, message.to_dict()):
            self._skipped += 1
            return

        results = await notification_router.dispatch(message)
        sent_any = any(r.get("status") == "sent" for r in results)
        if sent_any:
            self._dispatched += 1
        else:
            self._skipped += 1

        publisher = self._publisher or EventPublisher()
        await publisher.publish(
            EventType.NOTIFICATION_DISPATCHED,
            source=self.id,
            payload={
                "user_id": message.user_id,
                "message_type": message.message_type,
                "priority": message.priority,
                "symbol": message.symbol,
                "results": results,
                "summary": message.summary,
            },
            correlation_id=event.correlation_id if event else message.dedupe_key,
        )
        logger.info(
            "agent=%s action=dispatch user_id=%s type=%s results=%s",
            self.id,
            message.user_id,
            message.message_type,
            results,
        )

    def _resolve_user_ids(self, event_type: str, payload: dict[str, Any]) -> list[int]:
        if payload.get("user_id") is not None:
            return [int(payload["user_id"])]

        # Broadcast-style events: target users with watchlist match or all preference users
        symbol = str(payload.get("symbol") or "").upper()
        db = SessionLocal()
        try:
            if symbol:
                from app.models.user_watchlist import UserWatchlist

                rows = list(
                    db.scalars(
                        select(UserWatchlist.user_id).where(
                            UserWatchlist.symbol == symbol,
                            UserWatchlist.enabled.is_(True),
                        )
                    ).all()
                )
                if rows:
                    return sorted({int(u) for u in rows})

            prefs = PreferencesRepository(db).list_all_user_ids()
            if prefs:
                return prefs

            # Fall back to active users (cap)
            users = list(
                db.scalars(select(User.id).where(User.is_active.is_(True)).limit(50)).all()
            )
            return [int(u) for u in users]
        finally:
            db.close()

    def health(self) -> dict[str, Any]:
        base = super().health()
        return {
            **base,
            "dispatched": self._dispatched,
            "skipped": self._skipped,
            "router_sent": notification_router.sent,
            "router_failed": notification_router.failed,
            "router_skipped": notification_router.skipped,
        }
