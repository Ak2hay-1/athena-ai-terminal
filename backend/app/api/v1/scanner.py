"""
Scanner API — ranked realtime opportunity board.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.scanner import ScannerOpportunitiesResponse
from app.services.scanner_service import ScannerService

router = APIRouter(
    prefix="/scanner",
    tags=["Scanner"],
)


def get_scanner_service(db: Session = Depends(get_db)) -> ScannerService:
    return ScannerService(db)


@router.get(
    "/opportunities",
    response_model=ScannerOpportunitiesResponse,
    summary="Ranked scanner opportunities (batch)",
)
def get_scanner_opportunities(
    timeframe: str = Query("M15", description="Primary timeframe"),
    symbols: str | None = Query(
        None,
        description="Comma-separated symbols (defaults to SCANNER_SYMBOLS / watchlist)",
    ),
    use_watchlist: bool = Query(
        False,
        description="Prefer the authenticated user's enabled watchlist symbols",
    ),
    min_score: int | None = Query(
        None,
        ge=0,
        le=100,
        description="Minimum scanner score",
    ),
    signals: str | None = Query(
        None,
        description="Comma-separated signal filter (e.g. BUY,STRONG_BUY,SELL)",
    ),
    actionable_only: bool = Query(
        False,
        description="Exclude HOLD / NEUTRAL / NO_TRADE",
    ),
    limit: int | None = Query(
        None,
        ge=1,
        le=200,
        description="Max rows to return after ranking",
    ),
    user: User = Depends(get_current_active_user),
    service: ScannerService = Depends(get_scanner_service),
) -> ScannerOpportunitiesResponse:
    symbol_list = (
        [s.strip() for s in symbols.split(",") if s.strip()]
        if symbols
        else None
    )
    signal_list = (
        [s.strip() for s in signals.split(",") if s.strip()]
        if signals
        else None
    )
    return service.get_opportunities(
        timeframe=timeframe,
        user_id=user.id,
        symbols=symbol_list,
        use_watchlist=use_watchlist,
        min_score=min_score,
        signals=signal_list,
        actionable_only=actionable_only,
        limit=limit,
    )
