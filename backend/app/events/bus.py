"""
Asynchronous in-process event bus.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from collections import deque
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any

from app.core.logger import get_logger
from app.events.base import Event
from app.events.types import EventType

logger = get_logger("athena.events")

EventHandler = Callable[[Event], Awaitable[None] | None]


class AsyncEventBus:
    """
    Async pub/sub bus with history and error-isolated fan-out.
    """

    def __init__(self, history_size: int = 500) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: deque[Event] = deque(maxlen=max(1, history_size))
        self._lock = asyncio.Lock()
        self._queue_depth = 0
        self._events_published = 0
        self._dispatch_failures = 0

    @property
    def queue_depth(self) -> int:
        return self._queue_depth

    def metrics(self) -> dict[str, Any]:
        return {
            "events_published": self._events_published,
            "dispatch_failures": self._dispatch_failures,
            "queue_length": self._queue_depth,
            "subscriber_count": sum(len(v) for v in self._subscribers.values()),
            "history_size": len(self._history),
        }

    def subscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> None:
        key = str(event_type)
        if handler not in self._subscribers[key]:
            self._subscribers[key].append(handler)
            logger.info(
                "event_bus action=subscribe event_type=%s handlers=%s",
                key,
                len(self._subscribers[key]),
            )

    def unsubscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> None:
        key = str(event_type)
        handlers = self._subscribers.get(key)
        if not handlers:
            return
        try:
            handlers.remove(handler)
            logger.info(
                "event_bus action=unsubscribe event_type=%s handlers=%s",
                key,
                len(handlers),
            )
        except ValueError:
            return
        if not handlers:
            del self._subscribers[key]

    async def publish(self, event: Event) -> list[Any]:
        """
        Publish to subscribers of the event type.
        Returns handler results (exceptions preserved for inspection).
        """
        return await self._dispatch(event, broadcast=False)

    async def broadcast(self, event: Event) -> list[Any]:
        """
        Publish to all subscribers of every event type.
        """
        return await self._dispatch(event, broadcast=True)

    def history(self, limit: int = 50) -> list[Event]:
        if limit <= 0:
            return []
        items = list(self._history)
        return items[-limit:]

    async def _dispatch(
        self,
        event: Event,
        *,
        broadcast: bool,
    ) -> list[Any]:
        started = time.perf_counter()
        self._queue_depth += 1
        self._events_published += 1
        self._history.append(event)

        try:
            if broadcast:
                handlers: list[EventHandler] = []
                seen: set[int] = set()
                for group in self._subscribers.values():
                    for handler in group:
                        handler_id = id(handler)
                        if handler_id not in seen:
                            seen.add(handler_id)
                            handlers.append(handler)
            else:
                handlers = list(self._subscribers.get(str(event.type), []))

            logger.info(
                "event_bus action=publish event_id=%s type=%s source=%s "
                "handlers=%s broadcast=%s",
                event.id,
                event.type,
                event.source,
                len(handlers),
                broadcast,
            )

            if not handlers:
                return []

            tasks = [self._invoke(handler, event) for handler in handlers]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            failed = sum(1 for result in results if isinstance(result, Exception))
            self._dispatch_failures += failed

            duration_ms = (time.perf_counter() - started) * 1000
            status = "error" if failed else "ok"
            logger.info(
                "event_bus action=dispatch event_id=%s type=%s status=%s "
                "duration_ms=%.2f failures=%s",
                event.id,
                event.type,
                status,
                duration_ms,
                failed,
            )
            return list(results)
        finally:
            self._queue_depth = max(0, self._queue_depth - 1)

    async def _invoke(
        self,
        handler: EventHandler,
        event: Event,
    ) -> None:
        try:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            logger.exception(
                "event_bus action=handler_error event_id=%s type=%s",
                event.id,
                event.type,
            )
            raise


def _default_history_size() -> int:
    try:
        from app.core.settings import settings

        return int(settings.AGENTS_EVENT_HISTORY_SIZE)
    except Exception:
        return 500


event_bus = AsyncEventBus(history_size=_default_history_size())
