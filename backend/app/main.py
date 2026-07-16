"""
Athena AI Terminal.

Application Entry Point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.api.websocket import router as websocket_router
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
from app.scheduler.news_scheduler import (
    news_scheduler,
)


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

    logger.info("Initializing database...")

    if settings.APP_ENV == "development" and settings.DEBUG:
        Base.metadata.create_all(bind=engine)

    logger.info("Database initialized.")

    try:
        logger.info("Initializing MT5...")
        mt5_client.initialize()
        logger.info("MT5 initialized.")
    except Exception as exc:
        logger.warning(
            "MT5 initialization skipped: %s",
            exc,
        )

    try:
        scheduler.start()
        news_scheduler.start()
        logger.info("Schedulers started.")
    except Exception as exc:
        logger.warning(
            "Scheduler startup failed: %s",
            exc,
        )

    logger.info("Athena started successfully.")

    yield

    logger.info("Stopping Athena...")

    try:
        scheduler.shutdown()
        news_scheduler.shutdown()
        logger.info("Schedulers stopped.")
    except Exception:
        pass

    try:
        mt5_client.shutdown()
        logger.info("MT5 disconnected.")
    except Exception:
        pass

    logger.info("Athena stopped.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Athena AI Trading Terminal",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(websocket_router)


@app.get("/", tags=["System"])
async def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "status": "running",
    }
