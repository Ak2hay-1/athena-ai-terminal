"""
Market API.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.auth.dependencies import require_trader
from app.database.database import get_db
from app.models.user import User
from app.schemas.market import (
    MarketBackfillRequest,
    MarketBackfillResult,
    MarketCandleCreate,
    MarketCandleRead,
    MarketHistoryRequest,
    MarketQuote,
    MarketStatistics,
)
from app.services.market_service import MarketService

router = APIRouter(
    prefix="/market",
    tags=["Market"],
)


# ==========================================================
# Dependency
# ==========================================================

def get_market_service(
    db: Session = Depends(get_db),
) -> MarketService:
    """
    Market service dependency.
    """

    return MarketService(db)


# ==========================================================
# Create Candle
# ==========================================================

@router.post(
    "/candles",
    response_model=MarketCandleRead,
    summary="Create market candle",
    status_code=201,
)
def create_candle(
    payload: MarketCandleCreate,
    _: User = Depends(require_trader),
    service: MarketService = Depends(get_market_service),
):

    return service.create_candle(payload)


# ==========================================================
# Bulk Import
# ==========================================================

@router.post(
    "/candles/bulk",
    response_model=int,
    summary="Bulk import candles",
)
def bulk_insert(
    payload: list[MarketCandleCreate],
    _: User = Depends(require_trader),
    service: MarketService = Depends(get_market_service),
):

    return service.bulk_insert(payload)


# ==========================================================
# Latest Candle
# ==========================================================

@router.get(
    "/latest",
    response_model=MarketCandleRead,
    summary="Latest candle",
)
def latest_candle(
    symbol: str = Query(...),
    timeframe: str = Query(...),
    _: User = Depends(require_trader),
    service: MarketService = Depends(get_market_service),
):

    return service.get_latest(
        symbol,
        timeframe,
    )


# ==========================================================
# Latest Candles
# ==========================================================

@router.get(
    "/candles",
    response_model=list[MarketCandleRead],
    summary="Latest candles",
)
def latest_candles(
    symbol: str = Query(...),
    timeframe: str = Query(...),
    limit: int = Query(
        default=500,
        ge=1,
        le=10000,
    ),
    before: datetime | None = Query(
        default=None,
        description="Return candles strictly older than this timestamp (UTC).",
    ),
    _: User = Depends(require_trader),
    service: MarketService = Depends(get_market_service),
):

    return service.get_latest_candles(
        symbol,
        timeframe,
        limit,
        before=before,
    )


# ==========================================================
# History
# ==========================================================

@router.post(
    "/history",
    response_model=list[MarketCandleRead],
    summary="Historical candles",
)
def history(
    payload: MarketHistoryRequest,
    _: User = Depends(require_trader),
    service: MarketService = Depends(get_market_service),
):

    return service.get_history(
        payload.symbol,
        payload.timeframe,
        payload.start_time,
        payload.end_time,
    )


# ==========================================================
# Live Quotes
# ==========================================================

@router.get(
    "/quotes",
    response_model=list[MarketQuote],
    summary="Live market quotes",
)
def live_quotes(
    symbols: str = Query(
        ...,
        description="Comma-separated symbols, e.g. XAUUSD,EURUSD",
    ),
    timeframe: str = Query(
        default="M1",
        description="Fallback candle timeframe when tick is unavailable",
    ),
    _: User = Depends(require_trader),
    service: MarketService = Depends(get_market_service),
):
    symbol_list = [
        item.strip().upper()
        for item in symbols.split(",")
        if item.strip()
    ]
    return service.get_quotes(symbol_list, timeframe)


# ==========================================================
# Statistics
# ==========================================================

@router.get(
    "/statistics",
    response_model=MarketStatistics,
    summary="Market statistics",
)
def statistics(
    symbol: str = Query(...),
    timeframe: str = Query(...),
    _: User = Depends(require_trader),
    service: MarketService = Depends(get_market_service),
):

    return service.get_statistics(
        symbol,
        timeframe,
    )


# ==========================================================
# Backfill
# ==========================================================

@router.post(
    "/backfill",
    response_model=MarketBackfillResult,
    summary="Deep-backfill candles from MT5",
)
def backfill_candles(
    payload: MarketBackfillRequest,
    _: User = Depends(require_trader),
    service: MarketService = Depends(get_market_service),
):
    return service.backfill_candles(
        payload.symbol,
        payload.timeframe,
        payload.count,
    )


# ==========================================================
# Market Data Engine
# ==========================================================

@router.get(
    "/engine/status",
    summary="Market data engine status",
)
def engine_status(
    _: User = Depends(require_trader),
):
    from app.core.settings import settings
    from app.marketdata.service import market_data_service

    return {
        "enabled": settings.MARKET_ENGINE_ENABLED,
        **market_data_service.status(),
    }


# ==========================================================
# Multi-layer Cache
# ==========================================================

@router.get(
    "/cache/status",
    summary="Market cache status and metrics",
)
def cache_status(
    _: User = Depends(require_trader),
):
    from app.cache import cache_manager
    from app.core.settings import settings

    return {
        "enabled": settings.CACHE_ENABLED,
        **cache_manager.status(),
    }


@router.post(
    "/cache/refresh",
    response_model=list[MarketCandleRead],
    summary="Invalidate and refresh candles for a symbol/timeframe",
)
def cache_refresh(
    symbol: str = Query(...),
    timeframe: str = Query(...),
    _: User = Depends(require_trader),
):
    from app.cache import cache_manager

    payloads = cache_manager.on_manual_refresh(symbol, timeframe)
    return [MarketCandleRead.model_validate(p) for p in payloads]


@router.post(
    "/cache/invalidate",
    summary="Invalidate cache entries",
)
def cache_invalidate(
    symbol: str | None = Query(default=None),
    timeframe: str | None = Query(default=None),
    _: User = Depends(require_admin),
):
    from app.cache import cache_manager

    cache_manager.invalidate(
        symbol, timeframe, reason="api_invalidate"
    )
    return {"ok": True, "symbol": symbol, "timeframe": timeframe}


@router.post(
    "/cache/preload",
    summary="Schedule background preload for a chart",
)
def cache_preload(
    symbol: str = Query(...),
    timeframe: str = Query(...),
    _: User = Depends(require_trader),
):
    from app.cache import cache_manager

    cache_manager.preloader.on_chart_open(symbol, timeframe)
    return {"ok": True, "symbol": symbol.upper(), "timeframe": timeframe.upper()}


# ==========================================================
# Cleanup
# ==========================================================

@router.delete(
    "/cleanup",
    response_model=int,
    summary="Delete historical candles",
)
def cleanup(
    before: datetime = Query(...),
    _: User = Depends(require_admin),
    service: MarketService = Depends(get_market_service),
):

    return service.delete_before(
        before,
    )