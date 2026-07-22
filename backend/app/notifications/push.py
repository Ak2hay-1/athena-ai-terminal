"""
Push notification channel (FCM-shaped stub).
"""

from __future__ import annotations

import time

from app.core.settings import settings
from app.database.database import SessionLocal
from app.notifications.message import DeliveryResult
from app.notifications.message import NotificationMessage
from app.notifications.templates import format_text
from app.repositories.preferences_repository import PreferencesRepository


class PushChannel:
    name = "push"

    async def send(self, message: NotificationMessage) -> DeliveryResult:
        started = time.perf_counter()
        if not settings.NOTIFY_PUSH_ENABLED:
            return DeliveryResult(
                channel=self.name,
                status="skipped",
                error="push disabled",
            )

        db = SessionLocal()
        try:
            prefs = PreferencesRepository(db).get_for_user(message.user_id)
            token = prefs.push_device_token if prefs else None
        finally:
            db.close()

        if not token:
            return DeliveryResult(
                channel=self.name,
                status="skipped",
                error="push_device_token missing",
            )

        # Provider integration point — record as skipped until FCM credentials configured.
        _ = format_text(message)
        return DeliveryResult(
            channel=self.name,
            status="skipped",
            latency_ms=(time.perf_counter() - started) * 1000,
            error="push provider not configured",
        )
