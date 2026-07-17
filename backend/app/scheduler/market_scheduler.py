"""
Market Scheduler.

Runs periodic market data collection jobs for all configured pairs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.logger import logger
from app.core.settings import settings
from app.database.database import SessionLocal
from app.mt5.candle_collector import CandleCollector
from app.services.market_service import MarketService
from app.services.websocket_broadcast import broadcast_candle_update


def _serialize_jobs(scheduler: BackgroundScheduler) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []

    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append(
            {
                "id": job.id,
                "name": job.name or job.id,
                "next_run_time": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger),
            }
        )

    return jobs


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

            latest_candle = None
            try:
                latest_candle = market_service.get_latest(
                    symbol,
                    timeframe,
                )
            except Exception:
                latest_candle = None

            recommendation = None

            if inserted > 0:
                recommendation = market_service.analyze_latest(
                    symbol=symbol,
                    timeframe=timeframe,
                )

            if latest_candle is not None or recommendation is not None:
                broadcast_candle_update(
                    symbol=symbol,
                    timeframe=timeframe,
                    inserted=inserted,
                    recommendation=recommendation,
                    candle=latest_candle,
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

    def status(self) -> dict[str, Any]:
        return {
            "name": "market",
            "running": self.scheduler.running,
            "jobs": _serialize_jobs(self.scheduler) if self.scheduler.running else [],
        }

    def trigger_timeframe(self, timeframe: str) -> dict[str, Any]:
        job_id = f"collect_{timeframe.lower()}"
        job = self.scheduler.get_job(job_id)

        if job is None:
            raise ValueError(f"Unknown market job for timeframe {timeframe}")

        now = datetime.now(tz=self.scheduler.timezone)
        self.scheduler.modify_job(job_id, next_run_time=now)

        return {
            "triggered": job_id,
            "timeframe": timeframe,
            "next_run_time": now.isoformat(),
        }

    def trigger_job(self, job_id: str) -> dict[str, Any]:
        job = self.scheduler.get_job(job_id)

        if job is None:
            raise ValueError(f"Unknown market job: {job_id}")

        now = datetime.now(tz=self.scheduler.timezone)
        self.scheduler.modify_job(job_id, next_run_time=now)

        return {
            "triggered": job_id,
            "next_run_time": now.isoformat(),
        }

    def shutdown(self) -> None:

        if self.scheduler.running:

            self.scheduler.shutdown(
                wait=False,
            )

            logger.info(
                "Market Scheduler stopped"
            )


market_scheduler = MarketScheduler()
