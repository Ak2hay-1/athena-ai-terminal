"""
Main API Router.

Registers all API v1 endpoints.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter
from fastapi import Depends

from app.api.v1.admin import router as admin_router
from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.disclaimer import router as disclaimer_router
from app.api.v1.journal import router as journal_router
from app.api.v1.learning import router as learning_router
from app.api.v1.market import router as market_router
from app.api.v1.mt5 import router as mt5_router
from app.api.v1.news import router as news_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.preferences import router as preferences_router
from app.api.v1.recommendations import router as recommendation_router
from app.api.v1.risk import router as risk_router
from app.api.v1.scanner import router as scanner_router
from app.api.v1.trade import router as trade_router
from app.api.v1.watchlist import router as watchlist_router
from app.auth.dependencies import require_disclaimer_accepted
from app.database.database import check_database_connection

router = APIRouter(
    prefix="/api/v1",
)


@router.get(
    "/health",
    tags=["System"],
    summary="Health Check",
)
async def health():
    # Never run sync DB I/O on the event loop — pool waits would freeze all HTTP.
    database_ok = await asyncio.to_thread(check_database_connection)

    return {
        "status": "healthy" if database_ok else "unhealthy",
        "database": "connected" if database_ok else "disconnected",
        "service": "Athena AI Terminal",
        "version": "1.0.0",
    }


# Auth, preferences, notifications, and disclaimer remain available
# without prior disclaimer acceptance so users can accept and manage account.
router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(disclaimer_router)
router.include_router(preferences_router)
router.include_router(notifications_router)

_disclaimer_deps = [Depends(require_disclaimer_accepted)]

router.include_router(market_router, dependencies=_disclaimer_deps)
router.include_router(mt5_router, dependencies=_disclaimer_deps)
router.include_router(recommendation_router, dependencies=_disclaimer_deps)
router.include_router(scanner_router, dependencies=_disclaimer_deps)
router.include_router(ai_router, dependencies=_disclaimer_deps)
router.include_router(news_router, dependencies=_disclaimer_deps)
router.include_router(watchlist_router, dependencies=_disclaimer_deps)
router.include_router(learning_router, dependencies=_disclaimer_deps)
router.include_router(trade_router, dependencies=_disclaimer_deps)
router.include_router(journal_router, dependencies=_disclaimer_deps)
router.include_router(portfolio_router, dependencies=_disclaimer_deps)
router.include_router(risk_router, dependencies=_disclaimer_deps)
