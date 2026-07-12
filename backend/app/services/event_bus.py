"""
Simple Event Bus for Athena.

Used for communication between:

- Market Engine
- Indicator Engine
- AI Engine
- WebSocket
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable


class EventBus:

    def __init__(self):
        self._listeners = defaultdict(list)

    def subscribe(
        self,
        event: str,
        callback: Callable,
    ) -> None:

        self._listeners[event].append(callback)

    def emit(
        self,
        event: str,
        payload=None,
    ) -> None:

        for callback in self._listeners[event]:
            callback(payload)


event_bus = EventBus()