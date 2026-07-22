"""
Trading API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from app.ai.models import AIRecommendation
from app.auth.dependencies import require_trader
from app.core.logger import logger
from app.core.market_validation import validate_symbol
from app.core.settings import settings
from app.database.database import get_db
from app.models.user import User
from app.repositories.paper_position_repository import PaperPositionRepository
from app.trading.order_manager import order_manager

router = APIRouter(
    prefix="/trade",
    tags=["Trading"],
)


class TradeOrderRequest(BaseModel):
    symbol: str = Field(..., examples=["EURUSD"])
    signal: str = Field(..., examples=["BUY"])
    confidence: int = Field(default=75, ge=0, le=100)
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float = Field(default=2.0)
    confluence: int | None = Field(default=70)
    timeframe: str = Field(default="M1")
    volume: float = Field(default=0.01, gt=0, le=100)


@router.post(
    "/order",
    summary="Place a trade order",
)
def place_order(
    payload: TradeOrderRequest,
    user: User = Depends(require_trader),
):
    symbol = validate_symbol(payload.symbol)
    signal = payload.signal.upper()
    if signal == "STRONG_BUY":
        signal = "BUY"
    elif signal == "STRONG_SELL":
        signal = "SELL"

    recommendation = AIRecommendation(
        signal=signal,
        confidence=payload.confidence,
        entry=payload.entry,
        stop_loss=payload.stop_loss,
        take_profit=payload.take_profit,
        risk_reward=payload.risk_reward,
        confluence=payload.confluence,
        symbol=symbol,
        timeframe=payload.timeframe.upper(),
        reason=["Manual order request"],
    )

    try:
        open_positions = order_manager.positions(user_id=user.id) or []
        if len(open_positions) >= settings.MAX_OPEN_TRADES:
            return {
                "success": False,
                "reasons": ["Maximum open trades reached."],
            }
    except Exception:
        logger.exception("Failed to count open positions before place_order")

    return order_manager.execute(
        recommendation,
        volume=payload.volume,
        user_id=user.id,
        source="manual",
    )


@router.post(
    "/close/{ticket}",
    summary="Close an open trade",
)
def close_trade(
    ticket: int,
    user: User = Depends(require_trader),
):
    closed = order_manager.close(ticket, user_id=user.id)
    return {"success": closed}


@router.get(
    "/positions",
    summary="List open trades",
)
def list_positions(
    user: User = Depends(require_trader),
):
    return order_manager.positions(user_id=user.id)


@router.get(
    "/history",
    summary="List closed trades",
)
def list_trade_history(
    limit: int = Query(default=100, ge=1, le=500),
    user: User = Depends(require_trader),
    db: Session = Depends(get_db),
):
    rows = PaperPositionRepository(db).list_closed(user.id, limit=limit)
    return [
        {
            **row.to_trade_dict(),
            "id": row.id,
            "closed_at": row.closed_at.isoformat() if row.closed_at else None,
            "recommendation_id": row.recommendation_id,
        }
        for row in rows
    ]
