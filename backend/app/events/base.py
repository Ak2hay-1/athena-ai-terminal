"""
Agent event model.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field

from app.events.types import EventType


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Event(BaseModel):
    """
    Envelope for all agent-orchestrator events.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: EventType | str
    timestamp: datetime = Field(default_factory=_utc_now)
    source: str
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False}
