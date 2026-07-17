"""
Athena AI Terminal.

Application Entry Point.
"""

from __future__ import annotations

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
from app.scheduler.market_scheduler import (
    market_scheduler as scheduler,
)
from app.scheduler.news_scheduler import (
    news_scheduler,
)

def _agent_dbg(hypothesis_id: str, location: str, message: str, data: dict | None = None) -> None:
    # #region agent log
    try:
        import json
        import time
        from pathlib import Path

        Path(__file__).resolve().parents[2].joinpath("debug-9c9447.log").open(
            "a", encoding="utf-8"
        ).write(
            json.dumps(
                {
                    "sessionId": "9c9447",
                    "runId": "pre-fix",
                    "hypothesisId": hypothesis_id,
                    "location": location,
                    "message": message,
                    "data": data or {},
                    "timestamp": int(time.time() * 1000),
                }
            )
            + "\n"
        )
    except Exception:
        pass
    # #endregion


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

    # #region agent log
    _db_host = ""
    try:
        from urllib.parse import urlparse

        _db_host = urlparse(settings.DATABASE_URL.replace("+psycopg", "")).hostname or ""
    except Exception:
        _db_host = "parse_error"
    _agent_dbg(
        "C",
        "main.py:lifespan:start",
        "lifespan entered",
        {
            "app_env": settings.APP_ENV,
            "debug": settings.DEBUG,
            "will_create_all": settings.APP_ENV == "development" and settings.DEBUG,
            "db_host": _db_host,
        },
    )
    # #endregion

    logger.info("Initializing database...")

    if settings.APP_ENV == "development" and settings.DEBUG:
        # #region agent log
        _agent_dbg("C", "main.py:lifespan:before_create_all", "about to create_all", {})
        # #endregion
        Base.metadata.create_all(bind=engine)
        # #region agent log
        _agent_dbg("C", "main.py:lifespan:after_create_all", "create_all finished", {})
        # #endregion

    logger.info("Database initialized.")

    try:
        logger.info("Initializing MT5...")
        # #region agent log
        _agent_dbg("E", "main.py:lifespan:before_mt5", "about to initialize MT5", {})
        # #endregion
        mt5_client.initialize()
        # #region agent log
        _agent_dbg("E", "main.py:lifespan:after_mt5", "MT5 initialize returned", {})
        # #endregion
        logger.info("MT5 initialized.")
    except Exception as exc:
        logger.warning(
            "MT5 initialization skipped: %s",
            exc,
        )
        # #region agent log
        _agent_dbg(
            "E",
            "main.py:lifespan:mt5_error",
            "MT5 initialize raised",
            {"error": str(exc)[:200]},
        )
        # #endregion

    try:
        # #region agent log
        _agent_dbg("C", "main.py:lifespan:before_schedulers", "about to start schedulers", {})
        # #endregion
        scheduler.start()
        news_scheduler.start()
        logger.info("Schedulers started.")
        # #region agent log
        _agent_dbg("C", "main.py:lifespan:after_schedulers", "schedulers started", {})
        # #endregion
    except Exception as exc:
        logger.warning(
            "Scheduler startup failed: %s",
            exc,
        )

    try:
        import asyncio

        from app.services.websocket_broadcast import set_main_event_loop

        set_main_event_loop(asyncio.get_running_loop())
    except Exception as exc:
        logger.warning("Failed to bind WebSocket event loop: %s", exc)

    logger.info("Athena started successfully.")
    # #region agent log
    _agent_dbg("A", "main.py:lifespan:ready", "lifespan yielded; HTTP should serve", {})
    # #endregion

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
