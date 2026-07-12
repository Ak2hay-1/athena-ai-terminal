"""
Application startup and shutdown lifecycle.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logger import logger
from app.market.client import client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
    """

    logger.info("======================================")
    logger.info("Starting Athena Terminal")
    logger.info("Initializing application services...")

    try:
        if client.connect():
            logger.info("MetaTrader 5 connected successfully.")
        else:
            logger.warning("MetaTrader 5 is not connected.")
    except Exception as exc:
        logger.exception("Failed to initialize MT5: %s", exc)

    logger.info("Application started.")
    logger.info("======================================")

    yield

    logger.info("======================================")
    logger.info("Shutting down Athena Terminal...")

    try:
        client.shutdown()
        logger.info("MetaTrader 5 disconnected.")
    except Exception as exc:
        logger.exception("Error while shutting down MT5: %s", exc)

    logger.info("Shutdown complete.")
    logger.info("======================================")