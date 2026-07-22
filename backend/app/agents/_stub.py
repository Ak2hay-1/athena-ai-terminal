"""
Shared stub agent implementation (no domain logic).
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.core.logger import get_logger
from app.events.base import Event
from app.events.types import EventType

logger = get_logger("athena.agents.stub")


class StubAgent(BaseAgent):
    """
    Concrete-ready stub. Domain packages subclass and set ClassVars.
    """

    subscribed_events = [EventType.SYSTEM_TICK]

    async def handle_event(self, event: Event) -> None:
        logger.info(
            "agent=%s action=stub_handle event_id=%s type=%s",
            self.id,
            event.id,
            event.type,
        )
