"""
News event repository.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.news_event import NewsEvent
from app.repositories.base_repository import BaseRepository


class NewsRepository(BaseRepository[NewsEvent]):
    """
    Persistence for news events.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(db, NewsEvent)

    def get_by_external_id(
        self,
        external_id: str,
    ) -> NewsEvent | None:
        return (
            self.db.query(NewsEvent)
            .filter(NewsEvent.external_id == external_id)
            .first()
        )

    def get_latest_for_symbol(
        self,
        symbol: str,
        limit: int = 20,
    ) -> list[NewsEvent]:
        symbol = symbol.upper()
        return (
            self.db.query(NewsEvent)
            .filter(NewsEvent.symbols.contains([symbol]))
            .order_by(desc(NewsEvent.published_at))
            .limit(limit)
            .all()
        )

    def get_upcoming_high_impact(
        self,
        symbol: str,
        within_minutes: int,
    ) -> list[NewsEvent]:
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        window_end = now + timedelta(minutes=within_minutes)

        return (
            self.db.query(NewsEvent)
            .filter(NewsEvent.symbols.contains([symbol.upper()]))
            .filter(NewsEvent.impact == "HIGH")
            .filter(NewsEvent.published_at >= now)
            .filter(NewsEvent.published_at <= window_end)
            .order_by(NewsEvent.published_at)
            .all()
        )

    def get_calendar(
        self,
        limit: int = 50,
    ) -> list[NewsEvent]:
        return (
            self.db.query(NewsEvent)
            .order_by(desc(NewsEvent.published_at))
            .limit(limit)
            .all()
        )
