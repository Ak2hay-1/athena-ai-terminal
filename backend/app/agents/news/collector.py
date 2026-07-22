"""
News collector — reuses NewsService (no new RSS parsers).
"""

from __future__ import annotations

from typing import Any

from app.core.logger import get_logger
from app.database.database import SessionLocal
from app.services.news_service import NewsService

logger = get_logger("athena.agents.news")


def collect_news(*, sync: bool = True, limit: int = 50) -> list[dict[str, Any]]:
    """
    Optionally sync feeds, then return latest calendar/headline rows.
    """
    db = SessionLocal()
    try:
        service = NewsService(db)
        if sync:
            try:
                inserted = service.sync_feeds()
                logger.info("news_collector action=sync inserted=%s", inserted)
            except Exception:
                logger.exception("news_collector action=sync status=error")

        events = service.repository.get_calendar(limit=limit)
        items: list[dict[str, Any]] = []
        for event in events:
            items.append(
                {
                    "id": event.id,
                    "title": event.title,
                    "summary": event.summary,
                    "source": event.source,
                    "symbols": list(event.symbols or []),
                    "impact": (
                        event.impact.value
                        if hasattr(event.impact, "value")
                        else str(event.impact or "LOW")
                    ),
                    "sentiment_score": event.sentiment_score,
                    "published_at": (
                        event.published_at.isoformat()
                        if event.published_at
                        else None
                    ),
                }
            )
        return items
    finally:
        db.close()
