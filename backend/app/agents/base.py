"""
Abstract base agent for the orchestrator framework.
"""

from __future__ import annotations

import time
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import ClassVar

from app.core.logger import get_logger
from app.events.base import Event
from app.events.types import EventType

logger = get_logger("athena.agents")


class BaseAgent(ABC):
    """
    Every agent exposes identity, lifecycle, health, and metrics.
    """

    id: ClassVar[str]
    name: ClassVar[str]
    version: ClassVar[str] = "0.1.0"
    priority: ClassVar[int] = 100
    subscribed_events: ClassVar[list[EventType | str]] = []

    def __init__(self) -> None:
        self.enabled: bool = True
        self._started_at: datetime | None = None
        self._status: str = "created"
        self._last_execution: datetime | None = None
        self._error_count: int = 0
        self._events_processed: int = 0
        self._total_runtime_ms: float = 0.0
        self._failures: int = 0
        self._queue_depth: int = 0
        self._tool_manager: Any | None = None
        self._publisher: Any | None = None

    def bind_tools(self, tool_manager: Any) -> None:
        self._tool_manager = tool_manager

    def bind_publisher(self, publisher: Any) -> None:
        self._publisher = publisher

    async def initialize(self) -> None:
        self._started_at = datetime.now(timezone.utc)
        self._status = "running"
        logger.info("agent=%s action=initialize status=ok", self.id)

    async def shutdown(self) -> None:
        self._status = "stopped"
        logger.info("agent=%s action=shutdown status=ok", self.id)

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Process a single event. Subclasses implement domain behavior."""

    async def process_event(self, event: Event) -> None:
        """
        Instrumented wrapper around handle_event with error isolation metrics.
        """
        if not self.enabled:
            return

        self._queue_depth += 1
        started = time.perf_counter()
        status = "ok"
        try:
            await self.handle_event(event)
            self._events_processed += 1
        except Exception:
            status = "error"
            self._error_count += 1
            self._failures += 1
            logger.exception(
                "agent=%s action=handle_event event_id=%s status=error",
                self.id,
                event.id,
            )
            raise
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            self._total_runtime_ms += duration_ms
            self._last_execution = datetime.now(timezone.utc)
            self._queue_depth = max(0, self._queue_depth - 1)
            logger.info(
                "agent=%s action=handle_event event_id=%s status=%s "
                "duration_ms=%.2f",
                self.id,
                event.id,
                status,
                duration_ms,
            )

    def health(self) -> dict[str, Any]:
        uptime_seconds = 0.0
        if self._started_at is not None:
            uptime_seconds = (
                datetime.now(timezone.utc) - self._started_at
            ).total_seconds()

        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "status": self._status if self.enabled else "disabled",
            "enabled": self.enabled,
            "uptime": uptime_seconds,
            "last_execution": (
                self._last_execution.isoformat() if self._last_execution else None
            ),
            "error_count": self._error_count,
            "average_runtime": self._average_runtime_ms(),
        }

    def metrics(self) -> dict[str, Any]:
        memory_usage = 0
        try:
            import sys

            memory_usage = sys.getsizeof(self)
        except Exception:
            memory_usage = 0

        return {
            "id": self.id,
            "events_processed": self._events_processed,
            "processing_time": self._total_runtime_ms,
            "average_runtime": self._average_runtime_ms(),
            "failures": self._failures,
            "memory_usage": memory_usage,
            "queue_length": self._queue_depth,
        }

    def _average_runtime_ms(self) -> float:
        if self._events_processed <= 0:
            return 0.0
        return self._total_runtime_ms / self._events_processed
