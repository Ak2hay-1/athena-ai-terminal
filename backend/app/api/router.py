"""
Main API Router.

Registers all API v1 endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.market import router as market_router
from app.api.v1.mt5 import router as mt5_router
from app.api.v1.recommendations import router as recommendation_router
from app.database.database import check_database_connection

router = APIRouter(
    prefix="/api/v1",
)


# ==========================================================
# System
# ==========================================================

@router.get(
    "/health",
    tags=["System"],
    summary="Health Check",
)
async def health():
    """
    API health check.
    """

    database_ok = check_database_connection()

    return {
        "status": "healthy" if database_ok else "unhealthy",
        "database": "connected" if database_ok else "disconnected",
        "service": "Athena AI Terminal",
        "version": "1.0.0",
    }


# ==========================================================
# Authentication
# ==========================================================

router.include_router(
    auth_router,
)


# ==========================================================
# Market
# ==========================================================

router.include_router(
    market_router,
)


# ==========================================================
# MetaTrader 5
# ==========================================================

router.include_router(
    mt5_router,
)


# ==========================================================
# Recommendations
# ==========================================================

router.include_router(
    recommendation_router,
)


# ==========================================================
# Trading Engine
# ==========================================================

# from app.api.v1.trade import router as trade_router
# router.include_router(trade_router)


# ==========================================================
# Portfolio
# ==========================================================

# from app.api.v1.portfolio import router as portfolio_router
# router.include_router(portfolio_router)


# ==========================================================
# Risk Engine
# ==========================================================

# from app.api.v1.risk import router as risk_router
# router.include_router(risk_router)


# ==========================================================
# Pattern Engine
# ==========================================================

# from app.api.v1.pattern import router as pattern_router
# router.include_router(pattern_router)


# ==========================================================
# AI Engine
# ==========================================================

# from app.api.v1.ai import router as ai_router
# router.include_router(ai_router)


# ==========================================================
# Backtesting
# ==========================================================

# from app.api.v1.backtest import router as backtest_router
# router.include_router(backtest_router)


# ==========================================================
# WebSocket
# ==========================================================

# WebSocket routes are registered in app.main
# during application startup.
