"""
Thread-safe schedule of agent events onto the running asyncio loop.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.logger import get_logger
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType

logger = get_logger("athena.events.async_bridge")

_main_loop: asyncio.AbstractEventLoop | None = None


def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop


def schedule_publish(
    event_type: EventType | str,
    payload: dict[str, Any] | None = None,
    *,
    source: str = "trade",
    correlation_id: str | None = None,
) -> None:
    """
    Publish an event asynchronously from sync code (e.g. paper execution).
    Safe to call when no loop is running (no-op with debug log).
    """
    event = Event(
        type=EventType(str(event_type)),
        payload=payload or {},
        source=source,
        correlation_id=correlation_id,
    )

    try:
        loop = _main_loop or asyncio.get_running_loop()
    except RuntimeError:
        loop = _main_loop

    if loop is None or not loop.is_running():
        logger.debug(
            "async_bridge skip publish type=%s (no running loop)",
            event_type,
        )
        return

    async def _publish() -> None:
        try:
            await EventPublisher().publish_event(event)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "async_bridge publish failed type=%s err=%s",
                event_type,
                exc,
            )

    try:
        asyncio.run_coroutine_threadsafe(_publish(), loop)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "async_bridge schedule failed type=%s err=%s",
            event_type,
            exc,
        )
