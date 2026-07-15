"""
Market API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.market import (
    MarketCandleResponse,
    MarketResponse,
)
from app.services.market_service import (
    MarketService,
)

router = APIRouter(
    prefix="/market",
    tags=["Market"],
)


@router.get(
    "/candles/{symbol}",
    response_model=MarketResponse,
)
def latest_candles(
    symbol: str,
    timeframe: str = "M1",
    limit: int = 500,
    db: Session = Depends(get_db),
):

    service = MarketService(db)

    candles = service.latest(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )

    return MarketResponse(
        success=True,
        count=len(candles),
        candles=[
            MarketCandleResponse.model_validate(
                candle
            )
            for candle in candles
        ],
    )


@router.get("/count")
def candle_count(
    db: Session = Depends(get_db),
):

    service = MarketService(db)

    return {
        "count": service.count(),
    }