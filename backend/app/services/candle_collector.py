"""
Background Candle Collector.

Runs continuously and keeps PostgreSQL synchronized with MT5.
"""

from __future__ import annotations

import asyncio
import threading
import time

from app.core.logger import logger
from app.database.database import SessionLocal
from app.market.adapter import market
from app.services.market_service import MarketService
from app.websocket.manager import manager


class CandleCollector:
    """
    Background service responsible for collecting
    new candles and broadcasting live market data.
    """

    def __init__(self) -> None:
        self.running = False
        self.thread: threading.Thread | None = None

    def _broadcast_tick(self, symbol: str) -> None:
        """
        Broadcast latest tick to websocket clients.
        """
        tick = market.tick(symbol)

        if tick is None:
            return

        try:
            asyncio.run(
                manager.send(
                    {
                        "type": "tick",
                        "symbol": symbol,
                        "data": tick,
                    }
                )
            )
        except RuntimeError:
            # Ignore if event loop already exists
            pass

    def _worker(
        self,
        symbol: str,
        timeframe: str,
        interval: int,
    ) -> None:

        logger.info(
            "Market Collector started (%s %s)",
            symbol,
            timeframe,
        )

        while self.running:

            db = SessionLocal()

            try:

                service = MarketService(db)

                inserted = service.sync_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    count=5,
                )

                logger.info(
                    "%s %s -> %s new candle(s)",
                    symbol,
                    timeframe,
                    inserted,
                )

                self._broadcast_tick(symbol)

            except Exception as exc:
                logger.exception(exc)

            finally:
                db.close()

            time.sleep(interval)

        logger.info("Market Collector stopped.")

    def start(
        self,
        symbol: str = "XAUUSD",
        timeframe: str = "M1",
        interval: int = 60,
    ) -> None:

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._worker,
            args=(
                symbol,
                timeframe,
                interval,
            ),
            daemon=True,
        )

        self.thread.start()

    def stop(self) -> None:

        self.running = False

        if self.thread:
            self.thread.join(timeout=2)


collector = CandleCollector()