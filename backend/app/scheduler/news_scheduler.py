"""
News sync + continuous learning scheduler.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.logger import logger
from app.core.settings import settings
from app.database.database import SessionLocal
from app.services.learning_service import LearningService
from app.services.news_service import NewsService


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


class NewsScheduler:

    def __init__(self) -> None:

        self.scheduler = BackgroundScheduler(
            timezone=settings.SCHEDULER_TIMEZONE,
        )

    def sync_news(self) -> None:

        db = SessionLocal()

        try:

            inserted = NewsService(db).sync_feeds()

            logger.info(
                "News sync complete (%d new events)",
                inserted,
            )

        except Exception:

            logger.exception("News sync failed.")

        finally:

            db.close()

    def label_outcomes(self) -> None:

        db = SessionLocal()

        try:

            count = LearningService(db).run_labeling()

            logger.info(
                "Labeled %d recommendation outcomes",
                count,
            )

        except Exception:

            logger.exception("Outcome labeling failed.")

        finally:

            db.close()

    def refresh_analytics(self) -> None:

        db = SessionLocal()

        try:

            result = LearningService(db).refresh_analytics()

            logger.info("Learning analytics refreshed: %s", result)

        except Exception:

            logger.exception("Learning analytics refresh failed.")

        finally:

            db.close()

    def update_weights(self) -> None:

        db = SessionLocal()

        try:

            result = LearningService(db).update_confidence_weights(reason="scheduled")

            logger.info("Confidence weight update: %s", result)

        except Exception:

            logger.exception("Confidence weight update failed.")

        finally:

            db.close()

    def retrain_models(self) -> None:

        db = SessionLocal()

        try:

            results = LearningService(db).retrain_all()

            logger.info(
                "Retrained %d models",
                len(results),
            )

        except Exception:

            logger.exception("Model retrain failed.")

        finally:

            db.close()

    def start(self) -> None:

        self.scheduler.add_job(
            self.sync_news,
            trigger="interval",
            seconds=settings.NEWS_SYNC_INTERVAL,
            id="news_sync",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        self.scheduler.add_job(
            self.label_outcomes,
            trigger="interval",
            seconds=settings.LEARNING_LABEL_INTERVAL_SECONDS,
            id="outcome_labeling",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        if settings.LEARNING_ENABLED:

            self.scheduler.add_job(
                self.refresh_analytics,
                trigger="interval",
                seconds=settings.LEARNING_ANALYTICS_INTERVAL_SECONDS,
                id="learning_analytics",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )

            self.scheduler.add_job(
                self.update_weights,
                trigger="interval",
                seconds=settings.LEARNING_WEIGHT_UPDATE_INTERVAL_HOURS * 3600,
                id="learning_weights",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )

            interval = settings.LEARNING_RETRAIN_INTERVAL_HOURS * 3600

            self.scheduler.add_job(
                self.retrain_models,
                trigger="interval",
                seconds=interval,
                id="model_retrain",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )

        self.scheduler.start()

        logger.info("News/Learning scheduler started")

    def status(self) -> dict[str, Any]:
        return {
            "name": "news_learning",
            "running": self.scheduler.running,
            "jobs": _serialize_jobs(self.scheduler) if self.scheduler.running else [],
        }

    def trigger_job(self, job_id: str) -> dict[str, Any]:
        job = self.scheduler.get_job(job_id)

        if job is None:
            raise ValueError(f"Unknown news/learning job: {job_id}")

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


news_scheduler = NewsScheduler()
