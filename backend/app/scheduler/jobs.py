"""
Built-in agent orchestrator jobs.

Publishes SystemTick heartbeats onto the event bus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logger import get_logger
from app.events.publisher import EventPublisher
from app.events.types import EventType

if TYPE_CHECKING:
    from app.scheduler.scheduler import AgentScheduler

logger = get_logger("athena.agent_jobs")


async def publish_system_tick(
    *,
    interval: str,
    publisher: EventPublisher,
) -> None:
    await publisher.publish(
        EventType.SYSTEM_TICK,
        source="agent_scheduler",
        payload={"interval": interval},
    )
    logger.info(
        "agent_job action=system_tick interval=%s status=ok",
        interval,
    )


def register_default_agent_jobs(
    scheduler: AgentScheduler,
    publisher: EventPublisher,
) -> None:
    """
    Register every-minute / every-hour / every-day SystemTick jobs.
    """

    async def tick_minute() -> None:
        await publish_system_tick(interval="minute", publisher=publisher)

    async def tick_hour() -> None:
        await publish_system_tick(interval="hour", publisher=publisher)

    async def tick_day() -> None:
        await publish_system_tick(interval="day", publisher=publisher)

    scheduler.add_interval(
        tick_minute,
        seconds=60,
        job_id="agent_tick_minute",
        name="Agent SystemTick (every minute)",
    )
    scheduler.add_cron(
        tick_hour,
        minute=0,
        job_id="agent_tick_hour",
        name="Agent SystemTick (every hour)",
    )
    scheduler.add_cron(
        tick_day,
        hour=0,
        minute=0,
        job_id="agent_tick_day",
        name="Agent SystemTick (every day)",
    )
    logger.info("agent_job action=register_defaults count=3")
