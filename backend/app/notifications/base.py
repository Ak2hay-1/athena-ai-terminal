"""
Notification channel protocol.
"""

from __future__ import annotations

from typing import Protocol
from typing import runtime_checkable

from app.notifications.message import DeliveryResult
from app.notifications.message import NotificationMessage


@runtime_checkable
class NotificationChannel(Protocol):
    name: str

    async def send(self, message: NotificationMessage) -> DeliveryResult:
        ...
