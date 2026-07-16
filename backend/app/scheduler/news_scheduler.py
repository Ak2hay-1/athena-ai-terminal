"""
News sync scheduler.
"""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.logger import logger
from app.core.settings import settings
from app.database.database import SessionLocal
from app.learning.outcome_labeler import OutcomeLabeler
from app.services.learning_service import LearningService
from app.services.news_service import NewsService


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

            count = OutcomeLabeler(db).label_pending()

            logger.info(
                "Labeled %d recommendation outcomes",
                count,
            )

        except Exception:

            logger.exception("Outcome labeling failed.")

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
            seconds=900,
            id="outcome_labeling",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        if settings.LEARNING_ENABLED:

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

    def shutdown(self) -> None:

        if self.scheduler.running:

            self.scheduler.shutdown(
                wait=False,
            )


news_scheduler = NewsScheduler()
