"""
Background candle collector.
"""

from __future__ import annotations

import threading
import time

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.database.database import SessionLocal
from app.services.market_service import MarketService


class CandleCollector:

    def __init__(self):

        self.running = False
        self.thread = None

    def _worker(
        self,
        symbol: str,
        timeframe: str,
        interval: int,
    ):

        logger.info(
            "Collector started for %s %s",
            symbol,
            timeframe,
        )

        while self.running:

            db: Session = SessionLocal()

            try:

                service = MarketService(db)

                inserted = service.sync_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    count=5,
                )

                logger.info(
                    "%s %s -> %s new candles",
                    symbol,
                    timeframe,
                    inserted,
                )

            except Exception as exc:

                logger.exception(exc)

            finally:

                db.close()

            time.sleep(interval)

    def start(
        self,
        symbol: str = "XAUUSD",
        timeframe: str = "M1",
        interval: int = 60,
    ):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._worker,
            args=(symbol, timeframe, interval),
            daemon=True,
        )

        self.thread.start()

    def stop(self):

        self.running = False


collector = CandleCollector()