"""
Market Scheduler.

Runs all background jobs for Athena.
"""

from __future__ import annotations

import threading
import time

from app.core.logger import logger
from app.services.candle_collector import collector


class MarketScheduler:

    def __init__(self):

        self.running = False
        self.thread: threading.Thread | None = None

    def _worker(self):

        logger.info("Market Scheduler Started")

        collector.start(
            symbol="XAUUSD",
            timeframe="M1",
            interval=60,
        )

        while self.running:

            # Future jobs
            # Indicator Calculation
            # AI Analysis
            # News Update
            # Pattern Detection

            time.sleep(1)

        collector.stop()

        logger.info("Market Scheduler Stopped")

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._worker,
            daemon=True,
        )

        self.thread.start()

    def stop(self):

        self.running = False

        if self.thread:

            self.thread.join(timeout=2)


scheduler = MarketScheduler()