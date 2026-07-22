"""
Event subscriber facade.
"""

from __future__ import annotations

from app.events.bus import AsyncEventBus
from app.events.bus import EventHandler
from app.events.bus import event_bus
from app.events.types import EventType


class EventSubscriber:
    """
    Typed helper for subscribing handlers to the bus.
    """

    def __init__(self, bus: AsyncEventBus | None = None) -> None:
        self._bus = bus or event_bus
        self._bindings: list[tuple[str, EventHandler]] = []

    def subscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> None:
        key = str(event_type)
        self._bus.subscribe(key, handler)
        self._bindings.append((key, handler))

    def unsubscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> None:
        key = str(event_type)
        self._bus.unsubscribe(key, handler)
        self._bindings = [
            (bound_type, bound_handler)
            for bound_type, bound_handler in self._bindings
            if not (bound_type == key and bound_handler is handler)
        ]

    def unsubscribe_all(self) -> None:
        for event_type, handler in list(self._bindings):
            self._bus.unsubscribe(event_type, handler)
        self._bindings.clear()


subscriber = EventSubscriber()
