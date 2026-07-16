"""
Market Scheduler.

Runs periodic market data collection jobs for all configured pairs.
"""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.logger import logger
from app.core.settings import settings
from app.database.database import SessionLocal
from app.mt5.candle_collector import CandleCollector
from app.services.market_service import MarketService
from app.services.websocket_broadcast import broadcast_candle_update


class MarketScheduler:

    def __init__(self) -> None:

        self.scheduler = BackgroundScheduler(
            timezone=settings.SCHEDULER_TIMEZONE,
        )

    def collect_pair(
        self,
        symbol: str,
        timeframe: str,
    ) -> None:

        db = SessionLocal()

        try:

            collector = CandleCollector(db)

            market_service = MarketService(db)

            inserted = collector.collect(
                symbol,
                timeframe,
            )

            if inserted <= 0:
                return

            recommendation = market_service.analyze_latest(
                symbol=symbol,
                timeframe=timeframe,
            )

            broadcast_candle_update(
                symbol=symbol,
                timeframe=timeframe,
                inserted=inserted,
                recommendation=recommendation,
            )

        except Exception:

            logger.exception(
                "Collection failed for %s %s",
                symbol,
                timeframe,
            )

        finally:

            db.close()

    def start(self) -> None:

        scheduled: set[str] = set()

        for timeframe in settings.MARKET_TIMEFRAMES:

            interval = settings.COLLECTOR_INTERVALS.get(
                timeframe,
                settings.COLLECTOR_INTERVAL_SECONDS,
            )

            job_id = f"collect_{timeframe.lower()}"

            if job_id in scheduled:
                continue

            scheduled.add(job_id)

            self.scheduler.add_job(
                self._run_timeframe,
                trigger="interval",
                seconds=interval,
                id=job_id,
                kwargs={"timeframe": timeframe},
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )

        self.scheduler.start()

        logger.info(
            "Market Scheduler started for %d symbols x %d timeframes",
            len(settings.MARKET_SYMBOLS),
            len(settings.MARKET_TIMEFRAMES),
        )

    def _run_timeframe(
        self,
        timeframe: str,
    ) -> None:

        for symbol in settings.MARKET_SYMBOLS:

            try:

                self.collect_pair(
                    symbol,
                    timeframe,
                )

            except Exception:

                logger.exception(
                    "Isolated failure %s %s",
                    symbol,
                    timeframe,
                )

    def shutdown(self) -> None:

        if self.scheduler.running:

            self.scheduler.shutdown(
                wait=False,
            )

            logger.info(
                "Market Scheduler stopped"
            )


market_scheduler = MarketScheduler()
