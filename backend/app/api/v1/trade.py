"""
Trading API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import Field

from app.ai.models import AIRecommendation
from app.auth.dependencies import require_trader
from app.core.market_validation import validate_symbol
from app.core.settings import settings
from app.models.user import User
from app.trading.order_manager import order_manager
from app.trading.paper_execution import paper_execution

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


@router.post(
    "/order",
    summary="Place a paper trade order",
)
def place_order(
    payload: TradeOrderRequest,
    _: User = Depends(require_trader),
):
    symbol = validate_symbol(payload.symbol)

    recommendation = AIRecommendation(
        signal=payload.signal.upper(),
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

    open_positions = paper_execution.positions()

    if len(open_positions) >= settings.MAX_OPEN_TRADES:
        return {
            "success": False,
            "reasons": ["Maximum open trades reached."],
        }

    return order_manager.execute(recommendation)


@router.post(
    "/close/{ticket}",
    summary="Close an open paper trade",
)
def close_trade(
    ticket: int,
    _: User = Depends(require_trader),
):
    closed = order_manager.close(ticket)
    return {"success": closed}


@router.get(
    "/positions",
    summary="List open paper trades",
)
def list_positions(
    _: User = Depends(require_trader),
):
    return order_manager.positions()
