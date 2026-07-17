"""
Risk API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import Field

from app.auth.dependencies import require_trader
from app.core.settings import settings
from app.models.user import User
from app.trading.paper_execution import paper_execution

router = APIRouter(
    prefix="/risk",
    tags=["Risk"],
)


class RiskAssessmentRequest(BaseModel):
    symbol: str
    volume: float = Field(default=0.01, gt=0)


@router.get(
    "/limits",
    summary="Current risk limits",
)
def risk_limits(
    _: User = Depends(require_trader),
):
    return {
        "max_open_trades": settings.MAX_OPEN_TRADES,
        "max_risk_percent": settings.MAX_RISK_PERCENT,
        "risk_reward_ratio": settings.RISK_REWARD_RATIO,
        "min_rr": settings.MIN_RR,
        "preferred_rr": settings.PREFERRED_RR,
        "max_rr": settings.MAX_RR,
        "atr_multiplier": settings.ATR_MULTIPLIER,
        "atr_multipliers_by_style": settings.ATR_MULTIPLIERS_BY_STYLE,
        "min_stop_pips": settings.MIN_STOP_PIPS,
        "sl_buffer_atr_fraction": settings.SL_BUFFER_ATR_FRACTION,
        "min_sl_atr_fraction": settings.MIN_SL_ATR_FRACTION,
        "require_bos": settings.REQUIRE_BOS,
        "require_choch": settings.REQUIRE_CHOCH,
        "execution_provider": settings.EXECUTION_PROVIDER,
    }


@router.post(
    "/assess",
    summary="Assess trade risk",
)
def assess_risk(
    payload: RiskAssessmentRequest,
    _: User = Depends(require_trader),
):
    open_count = len(paper_execution.positions())

    allowed = open_count < settings.MAX_OPEN_TRADES

    return {
        "allowed": allowed,
        "open_positions": open_count,
        "max_open_trades": settings.MAX_OPEN_TRADES,
        "symbol": payload.symbol.upper(),
        "volume": payload.volume,
    }
