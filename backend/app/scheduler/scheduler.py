"""
Agent orchestrator scheduler (AsyncIOScheduler).

Does not replace market_scheduler or news_scheduler.
"""

from __future__ import annotations

from collections.abc import Awaitable
from collections.abc import Callable
from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger("athena.agent_scheduler")

JobFunc = Callable[..., Any] | Callable[..., Awaitable[Any]]


class AgentScheduler:
    """
    Cron / interval / one-time jobs for the agent framework.
    """

    def __init__(self, timezone: str | None = None) -> None:
        self._timezone = timezone or settings.SCHEDULER_TIMEZONE
        self._scheduler = AsyncIOScheduler(timezone=self._timezone)
        self._started = False

    @property
    def running(self) -> bool:
        return self._scheduler.running

    def start(self) -> None:
        if self._scheduler.running:
            return
        self._scheduler.start()
        self._started = True
        logger.info("agent_scheduler action=start timezone=%s", self._timezone)

    def shutdown(self, wait: bool = False) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            self._started = False
            logger.info("agent_scheduler action=shutdown")

    def add_interval(
        self,
        func: JobFunc,
        *,
        seconds: int | None = None,
        minutes: int | None = None,
        hours: int | None = None,
        job_id: str,
        name: str | None = None,
        kwargs: dict[str, Any] | None = None,
        replace_existing: bool = True,
    ) -> str:
        trigger = IntervalTrigger(
            seconds=seconds or 0,
            minutes=minutes or 0,
            hours=hours or 0,
            timezone=self._timezone,
        )
        self._scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name or job_id,
            kwargs=kwargs or {},
            replace_existing=replace_existing,
        )
        logger.info("agent_scheduler action=add_interval job_id=%s", job_id)
        return job_id

    def add_cron(
        self,
        func: JobFunc,
        *,
        job_id: str,
        name: str | None = None,
        minute: str | int = "*",
        hour: str | int = "*",
        day: str | int = "*",
        month: str | int = "*",
        day_of_week: str | int = "*",
        kwargs: dict[str, Any] | None = None,
        replace_existing: bool = True,
    ) -> str:
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone=self._timezone,
        )
        self._scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name or job_id,
            kwargs=kwargs or {},
            replace_existing=replace_existing,
        )
        logger.info("agent_scheduler action=add_cron job_id=%s", job_id)
        return job_id

    def add_once(
        self,
        func: JobFunc,
        *,
        run_at: datetime,
        job_id: str,
        name: str | None = None,
        kwargs: dict[str, Any] | None = None,
        replace_existing: bool = True,
    ) -> str:
        trigger = DateTrigger(run_date=run_at, timezone=self._timezone)
        self._scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name or job_id,
            kwargs=kwargs or {},
            replace_existing=replace_existing,
        )
        logger.info(
            "agent_scheduler action=add_once job_id=%s run_at=%s",
            job_id,
            run_at.isoformat(),
        )
        return job_id

    def remove(self, job_id: str) -> bool:
        job = self._scheduler.get_job(job_id)
        if job is None:
            return False
        self._scheduler.remove_job(job_id)
        logger.info("agent_scheduler action=remove job_id=%s", job_id)
        return True

    def list_jobs(self) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        for job in self._scheduler.get_jobs():
            next_run = getattr(job, "next_run_time", None)
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name or job.id,
                    "next_run_time": next_run.isoformat() if next_run else None,
                    "trigger": str(job.trigger),
                }
            )
        return jobs

    def status(self) -> dict[str, Any]:
        return {
            "running": self._scheduler.running,
            "timezone": self._timezone,
            "jobs": self.list_jobs(),
        }


agent_scheduler = AgentScheduler()
