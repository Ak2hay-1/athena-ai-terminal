"""
Application lifespan management.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logger import logger
from app.market.client import client
from app.services.market_scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown.
    """

    logger.info("=" * 80)
    logger.info("Starting Athena Terminal")
    logger.info("=" * 80)

    # Initialize MT5
    if client.connect():
        logger.info("MetaTrader 5 connected successfully.")
    else:
        logger.warning("MetaTrader 5 connection failed.")

    # Start background services
    scheduler.start()

    logger.info("Background scheduler started.")
    logger.info("Athena Terminal is ready.")

    yield

    logger.info("=" * 80)
    logger.info("Stopping Athena Terminal")

    scheduler.stop()
    client.shutdown()

    logger.info("Background scheduler stopped.")
    logger.info("MetaTrader 5 disconnected.")
    logger.info("Athena Terminal stopped.")
    logger.info("=" * 80)