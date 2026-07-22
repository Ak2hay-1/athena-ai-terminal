"""Unit tests for AgentScheduler."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from app.scheduler.scheduler import AgentScheduler


def test_add_interval_cron_once_and_remove() -> None:
    scheduler = AgentScheduler(timezone="UTC")

    def noop() -> None:
        return None

    scheduler.add_interval(
        noop,
        seconds=60,
        job_id="test_interval",
        name="interval job",
    )
    scheduler.add_cron(
        noop,
        minute=0,
        job_id="test_cron",
        name="cron job",
    )
    run_at = datetime.now(timezone.utc) + timedelta(hours=1)
    scheduler.add_once(
        noop,
        run_at=run_at,
        job_id="test_once",
        name="once job",
    )

    job_ids = {job["id"] for job in scheduler.list_jobs()}
    assert job_ids == {"test_interval", "test_cron", "test_once"}

    assert scheduler.remove("test_cron") is True
    assert scheduler.remove("missing") is False

    remaining = {job["id"] for job in scheduler.list_jobs()}
    assert remaining == {"test_interval", "test_once"}

    status = scheduler.status()
    assert status["timezone"] == "UTC"
    assert status["running"] is False
