"""
Athena AI Terminal.

Application Entry Point.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.api.websocket import handle_market_websocket
from app.core.exception_handlers import register_exception_handlers
from app.core.logger import logger
from app.core.logging_middleware import LoggingMiddleware
from app.core.request_id import RequestIDMiddleware
from app.core.settings import settings
from app.database.base import Base
from app.database.database import engine
from app.mt5.client import mt5_client
from app.agents.manager import agent_manager
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

    try:
        if settings.APP_ENV == "development" and settings.DEBUG:
            Base.metadata.create_all(bind=engine)
        logger.info("Database initialized.")
    except Exception as exc:
        logger.error(
            "Database initialization failed: %s",
            exc,
        )
        raise

    try:
        logger.info("Initializing MT5...")
        # MT5Client.initialize() bounds mt5.initialize() with a subprocess
        # timeout internally, so this can never hang app startup even if
        # the MT5 terminal is missing/unreachable.
        _mt5_ok = mt5_client.initialize()
        if _mt5_ok:
            logger.info("MT5 initialized.")
        else:
            logger.warning("MT5 initialization failed; continuing without MT5.")
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

    try:
        from app.events.async_bridge import set_event_loop
        from app.services.websocket_broadcast import set_main_event_loop

        loop = asyncio.get_running_loop()
        set_main_event_loop(loop)
        set_event_loop(loop)
    except Exception as exc:
        logger.warning("Failed to bind WebSocket event loop: %s", exc)

    if settings.MARKET_ENGINE_ENABLED:
        try:
            from app.marketdata.service import market_data_service

            market_data_service.start()
            logger.info("Market data engine started.")
        except Exception as exc:
            logger.warning("Market data engine startup failed: %s", exc)
    else:
        try:
            from app.mt5.tick_streamer import tick_streamer

            tick_streamer.start()
            logger.info("Tick streamer started.")
        except Exception as exc:
            logger.warning("Tick streamer startup failed: %s", exc)

    if settings.CACHE_ENABLED:
        try:
            from app.cache import cache_manager

            cache_manager.start()
            logger.info("Market cache manager started.")
        except Exception as exc:
            logger.warning("Cache manager startup failed: %s", exc)

    try:
        await agent_manager.start()
        logger.info("Agent manager started.")
    except Exception as exc:
        logger.warning(
            "Agent manager startup failed: %s",
            exc,
        )

    logger.info("Athena started successfully.")

    yield

    logger.info("Stopping Athena...")

    try:
        await agent_manager.shutdown()
        logger.info("Agent manager stopped.")
    except Exception:
        pass

    if settings.CACHE_ENABLED:
        try:
            from app.cache import cache_manager

            cache_manager.stop()
            logger.info("Market cache manager stopped.")
        except Exception:
            pass

    if settings.MARKET_ENGINE_ENABLED:
        try:
            from app.marketdata.service import market_data_service

            market_data_service.stop()
            logger.info("Market data engine stopped.")
        except Exception:
            pass
    else:
        try:
            from app.mt5.tick_streamer import tick_streamer

            tick_streamer.stop()
            logger.info("Tick streamer stopped.")
        except Exception:
            pass

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


@app.websocket("/ws")
async def market_websocket(websocket: WebSocket):
    """Primary market stream endpoint."""
    await handle_market_websocket(websocket)


@app.get("/", tags=["System"])
async def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "status": "running",
    }
