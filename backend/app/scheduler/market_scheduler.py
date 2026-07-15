"""
Market Scheduler.

Runs periodic market data collection jobs.
"""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.logger import logger
from app.core.settings import settings
from app.database.session import SessionLocal
from app.mt5.candle_collector import CandleCollector
from app.services.market_service import MarketService


class MarketScheduler:

    def __init__(self) -> None:

        self.scheduler = BackgroundScheduler()

    def collect_xauusd_m1(self) -> None:

        db = SessionLocal()

        try:

            collector = CandleCollector(db)

            market_service = MarketService(db)

            for symbol in settings.MARKET_SYMBOLS:

                inserted = collector.collect_m1(symbol)

                if inserted <= 0:
                    continue

                market_service.analyze_latest(
                    symbol=symbol,
                    timeframe="M1",
                )

        except Exception:

            logger.exception(
                "Market data collection failed."
            )

        finally:

            db.close()

    def start(self) -> None:

        self.scheduler.add_job(
            self.collect_xauusd_m1,
            trigger="interval",
            seconds=60,
            id="xauusd_m1",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        self.scheduler.start()

        logger.info(
            "Market Scheduler Started"
        )

    def shutdown(self) -> None:

        if self.scheduler.running:

            self.scheduler.shutdown(
                wait=False,
            )

            logger.info(
                "Market Scheduler Stopped"
            )


market_scheduler = MarketScheduler()
