"""
Portfolio API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import require_trader
from app.models.user import User
from app.trading.paper_execution import paper_execution

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


@router.get(
    "/summary",
    summary="Paper portfolio summary",
)
def portfolio_summary(
    _: User = Depends(require_trader),
):
    positions = paper_execution.positions()

    return {
        "open_positions": len(positions),
        "positions": positions,
        "execution_provider": "paper",
    }
