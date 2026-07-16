"""
AI analysis API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_trader
from app.core.market_validation import validate_symbol
from app.core.market_validation import validate_timeframe
from app.database.database import get_db
from app.models.user import User
from app.services.market_service import MarketService

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


def get_market_service(
    db: Session = Depends(get_db),
) -> MarketService:
    return MarketService(db)


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
