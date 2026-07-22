"""
Event publisher facade.
"""

from __future__ import annotations

from typing import Any

from app.events.base import Event
from app.events.bus import AsyncEventBus
from app.events.bus import event_bus
from app.events.types import EventType


class EventPublisher:
    """
    Typed helper for publishing events onto the bus.
    """

    def __init__(self, bus: AsyncEventBus | None = None) -> None:
        self._bus = bus or event_bus

    async def publish(
        self,
        event_type: EventType | str,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Event:
        event = Event(
            type=event_type,
            source=source,
            payload=payload or {},
            correlation_id=correlation_id,
            metadata=metadata or {},
        )
        await self._bus.publish(event)
        return event

    async def publish_event(self, event: Event) -> Event:
        await self._bus.publish(event)
        return event

    async def broadcast(self, event: Event) -> Event:
        await self._bus.broadcast(event)
        return event


publisher = EventPublisher()
