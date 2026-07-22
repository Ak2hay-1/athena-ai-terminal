"""
Structured notification message.
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from typing import Any


MESSAGE_TYPES = (
    "Trade Signal",
    "Trade Closed",
    "SL Hit",
    "TP Hit",
    "Risk Warning",
    "Portfolio Update",
    "Daily Summary",
    "Weekly Summary",
    "Monthly Report",
    "Breaking News",
    "Market Alert",
)

PRIORITIES = ("Critical", "High", "Medium", "Low")


@dataclass
class NotificationMessage:
    user_id: int
    message_type: str
    priority: str
    summary: str
    confidence: float | None = None
    reasoning: list[str] = field(default_factory=list)
    risk: str | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    evidence: list[str] = field(default_factory=list)
    action: str | None = None
    symbol: str | None = None
    side: str | None = None
    dedupe_key: str | None = None
    channel_hint: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["type"] = self.message_type
        return data


@dataclass
class DeliveryResult:
    channel: str
    status: str  # sent | failed | skipped
    latency_ms: float | None = None
    error: str | None = None
    external_id: str | None = None
