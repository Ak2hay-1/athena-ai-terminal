"""
Portfolio API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import require_trader
from app.models.user import User
from app.trading.order_manager import order_manager

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


@router.get(
    "/summary",
    summary="Portfolio summary",
)
def portfolio_summary(
    user: User = Depends(require_trader),
):
    positions = order_manager.positions(user_id=user.id)

    return {
        "open_positions": len(positions),
        "positions": positions,
        "execution_provider": order_manager.provider,
    }
