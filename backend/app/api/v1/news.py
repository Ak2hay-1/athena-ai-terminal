"""
News API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_viewer
from app.core.market_validation import validate_symbol
from app.database.database import get_db
from app.models.user import User
from app.services.news_service import NewsService

router = APIRouter(
    prefix="/news",
    tags=["News"],
)


def get_news_service(
    db: Session = Depends(get_db),
) -> NewsService:
    return NewsService(db)


@router.get(
    "/latest",
    summary="Latest news for a symbol",
)
def latest_news(
    symbol: str = Query(default="XAUUSD"),
    limit: int = Query(default=20, ge=1, le=100),
    _: User = Depends(require_viewer),
    service: NewsService = Depends(get_news_service),
):
    symbol = validate_symbol(symbol)
    events = service.repository.get_latest_for_symbol(
        symbol,
        limit,
    )

    return [
        {
            "id": event.id,
            "title": event.title,
            "summary": event.summary,
            "source": event.source,
            "symbols": event.symbols,
            "impact": event.impact,
            "sentiment_score": event.sentiment_score,
            "published_at": event.published_at,
        }
        for event in events
    ]


@router.get(
    "/calendar",
    summary="Economic calendar events",
)
def calendar(
    limit: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_viewer),
    service: NewsService = Depends(get_news_service),
):
    events = service.repository.get_calendar(limit)

    return [
        {
            "id": event.id,
            "title": event.title,
            "symbols": event.symbols,
            "impact": event.impact,
            "published_at": event.published_at,
        }
        for event in events
    ]


@router.get(
    "/context",
    summary="News context used in analysis",
)
def news_context(
    symbol: str = Query(default="XAUUSD"),
    _: User = Depends(require_viewer),
    service: NewsService = Depends(get_news_service),
):
    symbol = validate_symbol(symbol)
    return service.get_context_for_symbol(symbol)


@router.post(
    "/sync",
    summary="Trigger news sync",
)
def sync_news(
    _: User = Depends(require_viewer),
    service: NewsService = Depends(get_news_service),
):
    inserted = service.sync_feeds()
    return {"inserted": inserted}
