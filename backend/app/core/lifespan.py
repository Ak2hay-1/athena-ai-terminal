from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logger import logger
from app.market.client import client
from app.services.candle_collector import collector


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting Athena Terminal...")

    client.connect()

    collector.start(
        symbol="XAUUSD",
        timeframe="M1",
        interval=60,
    )

    logger.info("Market Collector Started")

    yield

    collector.stop()

    client.shutdown()

    logger.info("Athena Shutdown Complete")