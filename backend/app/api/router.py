"""
Main API Router.

Registers all API v1 endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.learning import router as learning_router
from app.api.v1.market import router as market_router
from app.api.v1.mt5 import router as mt5_router
from app.api.v1.news import router as news_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.recommendations import router as recommendation_router
from app.api.v1.risk import router as risk_router
from app.api.v1.trade import router as trade_router
from app.api.v1.watchlist import router as watchlist_router
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
    database_ok = check_database_connection()

    return {
        "status": "healthy" if database_ok else "unhealthy",
        "database": "connected" if database_ok else "disconnected",
        "service": "Athena AI Terminal",
        "version": "1.0.0",
    }


router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(market_router)
router.include_router(mt5_router)
router.include_router(recommendation_router)
router.include_router(ai_router)
router.include_router(news_router)
router.include_router(watchlist_router)
router.include_router(learning_router)
router.include_router(trade_router)
router.include_router(portfolio_router)
router.include_router(risk_router)
