"""
Market API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.market_service import MarketService

router = APIRouter(
    prefix="/market",
    tags=["Market"],
)


@router.get("/symbols")
def symbols(
    db: Session = Depends(get_db),
):
    service = MarketService(db)
    return service.symbols()


@router.get("/tick/{symbol}")
def tick(
    symbol: str,
    db: Session = Depends(get_db),
):
    service = MarketService(db)
    return service.tick(symbol)


@router.get("/candles/{symbol}")
def candles(
    symbol: str,
    timeframe: str = "M5",
    limit: int = 500,
    db: Session = Depends(get_db),
):
    service = MarketService(db)

    return service.latest(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )


@router.post("/sync/{symbol}")
def sync(
    symbol: str,
    timeframe: str = "M5",
    count: int = 500,
    db: Session = Depends(get_db),
):
    service = MarketService(db)

    inserted = service.sync_candles(
        symbol=symbol,
        timeframe=timeframe,
        count=count,
    )

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "inserted": inserted,
    }