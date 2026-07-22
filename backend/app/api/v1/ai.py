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
from app.ai.services.chat_service import chat_service
from app.ai.services.indicator_explainer import indicator_explainer
from app.ai.services.session_summary_service import session_summary_service
from app.ai.services.strategy_teacher import strategy_teacher
from app.ai.services.trade_explainer import trade_explainer
from app.auth.dependencies import require_trader
from app.auth.dependencies import require_viewer
from app.core.market_validation import validate_symbol
from app.core.market_validation import validate_timeframe
from app.database.database import get_db
from app.models.user import User
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.ai import ChatRequest
from app.schemas.ai import EmbeddingsRequest
from app.schemas.ai import ExplainIndicatorRequest
from app.schemas.ai import ExplainTradeRequest
from app.schemas.ai import MarketSummaryRequest
from app.schemas.ai import NewsSummaryRequest
from app.schemas.ai import SessionSummaryRequest
from app.schemas.ai import TeachRequest
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
    result = chat_service.chat(messages, context=context)
    return {
        "success": result.success,
        "data": result.model_dump(),
        "message": result.message,
    }


@router.post(
    "/explain-trade",
    summary="Explain a frozen Athena recommendation",
)
def explain_trade(
    body: ExplainTradeRequest,
    _: User = Depends(require_viewer),
    db: Session = Depends(get_db),
    market_service: MarketService = Depends(get_market_service),
):
    if body.snapshot:
        result = ai_service.explain_trade_from_snapshot(body.snapshot)
        return {
            "success": result.success,
            "data": result.model_dump(),
            "message": result.message,
        }

    if body.recommendation_id is not None:
        row = RecommendationRepository(db).get_by_id(body.recommendation_id)
        if row is None:
            return {
                "success": False,
                "message": "Recommendation not found.",
            }
        snapshot = {
            "id": row.id,
            "symbol": row.symbol,
            "timeframe": row.timeframe,
            "signal": row.signal,
            "confidence": row.confidence,
            "entry_price": row.entry_price,
            "entry_type": getattr(row, "entry_type", None),
            "stop_loss": row.stop_loss,
            "take_profit": row.take_profit,
            "risk_reward": row.risk_reward,
            "sl_reason": getattr(row, "sl_reason", None),
            "tp_reason": getattr(row, "tp_reason", None),
            "reason": getattr(row, "reasoning", None) or getattr(row, "reason", None),
            "status": row.status,
            "trade_probability": getattr(row, "trade_probability", None),
            "trade_quality": getattr(row, "trade_quality", None),
            "confidence_breakdown": getattr(row, "confidence_breakdown", None),
            "institutional_checklist": getattr(row, "institutional_checklist", None),
            "created_at": str(row.created_at) if row.created_at else None,
        }
        result = ai_service.explain_trade_from_snapshot(snapshot)
        return {
            "success": result.success,
            "data": result.model_dump(),
            "message": result.message,
        }

    if body.symbol and body.timeframe:
        symbol = validate_symbol(body.symbol)
        timeframe = validate_timeframe(body.timeframe)
        context = market_service.build_ai_market_context(symbol, timeframe)
        if context is None:
            return {
                "success": False,
                "message": "Not enough market data for explanation.",
            }
        result = trade_explainer.explain(context)
        return {
            "success": result.success,
            "data": result.model_dump(),
            "message": result.message,
        }

    return {
        "success": False,
        "message": "Provide recommendation_id, snapshot, or symbol+timeframe.",
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
    "/explain-indicator",
    summary="Educational indicator help",
)
def explain_indicator(
    body: ExplainIndicatorRequest,
    _: User = Depends(require_viewer),
    market_service: MarketService = Depends(get_market_service),
):
    context = None
    if body.symbol and body.timeframe:
        symbol = validate_symbol(body.symbol)
        timeframe = validate_timeframe(body.timeframe)
        context = market_service.build_ai_market_context(symbol, timeframe)

    result = indicator_explainer.explain(body.topic, context)
    return {
        "success": result.success,
        "data": result.model_dump(),
        "message": result.message,
    }


@router.post(
    "/teach",
    summary="Strategy teacher lesson",
)
def teach(
    body: TeachRequest,
    _: User = Depends(require_viewer),
):
    result = strategy_teacher.teach(body.topic)
    return {
        "success": result.success,
        "data": result.model_dump(),
        "message": result.message,
    }


@router.post(
    "/session-summary",
    summary="Trading session summary",
)
def session_summary(
    body: SessionSummaryRequest,
    _: User = Depends(require_viewer),
):
    stats = body.model_dump(exclude_none=True)
    result = session_summary_service.summarize(stats)
    return {
        "success": result.success,
        "data": result.model_dump(),
        "message": result.message,
    }


@router.get(
    "/health",
    summary="AI provider health and models",
)
def ai_health(_: User = Depends(require_viewer)):
    result = ai_service.health()
    return {
        "success": result.healthy,
        "data": result.model_dump(),
        "message": result.message,
    }


@router.get(
    "/models",
    summary="List available AI models (Ollama tags when local)",
)
def ai_models(_: User = Depends(require_viewer)):
    models = ai_service.list_models()
    health = ai_service.health()
    return {
        "success": True,
        "data": {
            "provider": health.provider,
            "active_model": health.model,
            "models": models,
        },
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
