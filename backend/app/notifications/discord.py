"""
Discord webhook notification channel.
"""

from __future__ import annotations

import time

import httpx

from app.core.settings import settings
from app.database.database import SessionLocal
from app.notifications.message import DeliveryResult
from app.notifications.message import NotificationMessage
from app.notifications.templates import format_text
from app.repositories.preferences_repository import PreferencesRepository


class DiscordChannel:
    name = "discord"

    async def send(self, message: NotificationMessage) -> DeliveryResult:
        started = time.perf_counter()
        webhook = settings.NOTIFY_DISCORD_WEBHOOK_URL
        if not settings.NOTIFY_DISCORD_ENABLED:
            return DeliveryResult(
                channel=self.name,
                status="skipped",
                error="discord disabled",
            )

        db = SessionLocal()
        try:
            prefs = PreferencesRepository(db).get_for_user(message.user_id)
            if prefs and prefs.discord_webhook_url:
                webhook = prefs.discord_webhook_url
        finally:
            db.close()

        if not webhook:
            return DeliveryResult(
                channel=self.name,
                status="skipped",
                error="discord webhook missing",
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook,
                    json={"content": format_text(message)[:1900]},
                )
            latency = (time.perf_counter() - started) * 1000
            if response.status_code >= 400:
                return DeliveryResult(
                    channel=self.name,
                    status="failed",
                    latency_ms=latency,
                    error=response.text[:500],
                )
            return DeliveryResult(
                channel=self.name,
                status="sent",
                latency_ms=latency,
            )
        except Exception as exc:  # noqa: BLE001
            return DeliveryResult(
                channel=self.name,
                status="failed",
                latency_ms=(time.perf_counter() - started) * 1000,
                error=str(exc),
            )
