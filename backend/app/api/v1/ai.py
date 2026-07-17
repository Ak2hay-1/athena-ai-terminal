"""
AI analysis API.

Business logic calls ai_service only — never provider SDKs.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.ai.schemas.context import ChatMessage
from app.ai.schemas.context import NewsItem
from app.ai.services.ai_service import ai_service
from app.auth.dependencies import require_trader
from app.auth.dependencies import require_viewer
from app.core.market_validation import validate_symbol
from app.core.market_validation import validate_timeframe
from app.database.database import get_db
from app.models.user import User
from app.schemas.ai import ChatRequest
from app.schemas.ai import EmbeddingsRequest
from app.schemas.ai import MarketSummaryRequest
from app.schemas.ai import NewsSummaryRequest
from app.services.market_service import MarketService
from app.services.news_service import NewsService

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


def get_market_service(
    db: Session = Depends(get_db),
) -> MarketService:
    return MarketService(db)


def get_news_service(
    db: Session = Depends(get_db),
) -> NewsService:
    return NewsService(db)


@router.post(
    "/analyze",
    summary="Run on-demand AI analysis",
)
def analyze(
    symbol: str = Query(default="XAUUSD"),
    timeframe: str = Query(default="M1"),
    _: User = Depends(require_trader),
    service: MarketService = Depends(get_market_service),
):
    symbol = validate_symbol(symbol)
    timeframe = validate_timeframe(timeframe)

    recommendation = service.analyze_latest(
        symbol=symbol,
        timeframe=timeframe,
    )

    if recommendation is None:
        return {
            "success": False,
            "message": "Analysis could not be completed.",
        }

    return {
        "success": True,
        "recommendation": recommendation.model_dump(),
    }


@router.post(
    "/chat",
    summary="Chat with Athena AI",
)
def chat(
    body: ChatRequest,
    _: User = Depends(require_trader),
    market_service: MarketService = Depends(get_market_service),
):
    context = None
    if body.symbol and body.timeframe:
        symbol = validate_symbol(body.symbol)
        timeframe = validate_timeframe(body.timeframe)
        context = market_service.build_ai_market_context(symbol, timeframe)

    messages = [
        ChatMessage(role=message.role, content=message.content)
        for message in body.messages
    ]
    result = ai_service.chat(messages, context=context)
    return {
        "success": result.success,
        "data": result.model_dump(),
        "message": result.message,
    }


@router.post(
    "/market-summary",
    summary="Generate structured market summary",
)
def market_summary(
    body: MarketSummaryRequest,
    _: User = Depends(require_viewer),
    market_service: MarketService = Depends(get_market_service),
):
    symbol = validate_symbol(body.symbol)
    timeframe = validate_timeframe(body.timeframe)
    context = market_service.build_ai_market_context(symbol, timeframe)
    if context is None:
        return {
            "success": False,
            "message": "Not enough market data for summary.",
        }

    result = ai_service.generate_market_summary(context)
    return {
        "success": result.success,
        "data": result.model_dump(),
        "message": result.message,
    }


@router.post(
    "/news-summary",
    summary="Summarize recent news for a symbol",
)
def news_summary(
    body: NewsSummaryRequest,
    _: User = Depends(require_viewer),
    news_service: NewsService = Depends(get_news_service),
    market_service: MarketService = Depends(get_market_service),
):
    symbol = validate_symbol(body.symbol)
    events = news_service.repository.get_latest_for_symbol(
        symbol,
        body.limit,
    )
    items = [
        NewsItem(
            title=event.title,
            summary=event.summary or "",
            sentiment=str(event.sentiment_score)
            if event.sentiment_score is not None
            else None,
            impact=event.impact,
            source=event.source,
        )
        for event in events
    ]
    context = market_service.build_ai_market_context(symbol, "M5")
    result = ai_service.summarize_news(items, context=context)
    return {
        "success": result.success,
        "data": result.model_dump(),
        "message": result.message,
    }


@router.post(
    "/embeddings",
    summary="Generate text embeddings",
)
def embeddings(
    body: EmbeddingsRequest,
    _: User = Depends(require_trader),
):
    result = ai_service.generate_embeddings(body.texts)
    return {
        "success": result.success,
        "data": result.model_dump(),
        "message": result.message,
    }
