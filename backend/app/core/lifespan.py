"""
FastAPI Lifespan.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logger import logger
from app.mt5.client import mt5_client
from app.mt5.tick_streamer import tick_streamer
from app.scheduler.market_scheduler import (
    market_scheduler,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    """
    Application lifecycle.
    """

    logger.info("=" * 80)
    logger.info("Starting Athena Terminal")
    logger.info("=" * 80)

    # -------------------------------------------------
    # MT5
    # -------------------------------------------------

    if mt5_client.initialize():

        logger.info(
            "MetaTrader 5 connected successfully."
        )

    else:

        logger.warning(
            "MetaTrader 5 connection failed."
        )

    # -------------------------------------------------
    # Scheduler + tick stream
    # -------------------------------------------------

    market_scheduler.start()
    tick_streamer.start()

    logger.info(
        "Athena Terminal is ready."
    )

    yield

    # -------------------------------------------------
    # Shutdown
    # -------------------------------------------------

    logger.info(
        "Stopping Athena Terminal..."
    )

    tick_streamer.stop()
    market_scheduler.stop()

    mt5_client.shutdown()

    logger.info(
        "Athena stopped successfully."
    )
