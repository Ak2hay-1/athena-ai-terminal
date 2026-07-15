"""
Athena AI Terminal.

Application Entry Point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.core.exception_handlers import register_exception_handlers
from app.core.logger import logger
from app.core.logging_middleware import LoggingMiddleware
from app.core.request_id import RequestIDMiddleware
from app.core.settings import settings
from app.database.base import Base
from app.database.database import engine
from app.mt5.client import mt5_client
from app.scheduler.market_scheduler import (
    market_scheduler as scheduler,
)


# ==========================================================
# Lifespan
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup / shutdown.
    """

    logger.info("=" * 60)
    logger.info("Starting Athena AI Terminal")
    logger.info("Environment : %s", settings.APP_ENV)
    logger.info("Version     : %s", settings.APP_VERSION)
    logger.info("=" * 60)

    # ------------------------------------------------------
    # Database
    # ------------------------------------------------------

    logger.info("Initializing database...")

    # Development only.
    # Remove after production migration workflow is finalized.
    Base.metadata.create_all(bind=engine)

    logger.info("Database initialized.")

    # ------------------------------------------------------
    # MT5
    # ------------------------------------------------------

    try:

        logger.info("Initializing MT5...")

        mt5_client.initialize()

        logger.info("MT5 initialized.")

    except Exception as exc:

        logger.warning(
            "MT5 initialization skipped: %s",
            exc,
        )

    # ------------------------------------------------------
    # Scheduler
    # ------------------------------------------------------

    try:

        scheduler.start()

        logger.info("Scheduler started.")

    except Exception as exc:

        logger.warning(
            "Scheduler startup failed: %s",
            exc,
        )

    logger.info("Athena started successfully.")

    yield

    # ======================================================
    # Shutdown
    # ======================================================

    logger.info("Stopping Athena...")

    try:

        scheduler.shutdown()

        logger.info("Scheduler stopped.")

    except Exception:

        pass

    try:

        mt5_client.shutdown()

        logger.info("MT5 disconnected.")

    except Exception:

        pass

    logger.info("Athena stopped.")


# ==========================================================
# FastAPI
# ==========================================================

app = FastAPI(

    title=settings.APP_NAME,

    version=settings.APP_VERSION,

    description="Athena AI Trading Terminal",

    docs_url="/docs",

    redoc_url="/redoc",

    openapi_url="/openapi.json",

    lifespan=lifespan,

)

# ==========================================================
# Exception Handlers
# ==========================================================

register_exception_handlers(app)

# ==========================================================
# Middleware
# ==========================================================

app.add_middleware(
    RequestIDMiddleware,
)

app.add_middleware(
    LoggingMiddleware,
)

app.add_middleware(

    CORSMiddleware,

    allow_origins=settings.BACKEND_CORS_ORIGINS,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)

# ==========================================================
# API
# ==========================================================

app.include_router(router)

# ==========================================================
# Root
# ==========================================================

@app.get(
    "/",
    tags=["System"],
)
async def root():

    return {

        "application": settings.APP_NAME,

        "version": settings.APP_VERSION,

        "environment": settings.APP_ENV,

        "status": "running",

    }
