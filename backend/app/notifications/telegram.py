"""
Telegram notification channel.
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


class TelegramChannel:
    name = "telegram"

    async def send(self, message: NotificationMessage) -> DeliveryResult:
        started = time.perf_counter()
        if not settings.NOTIFY_TELEGRAM_ENABLED or not settings.NOTIFY_TELEGRAM_BOT_TOKEN:
            return DeliveryResult(
                channel=self.name,
                status="skipped",
                error="telegram disabled or token missing",
            )

        chat_id = message.extra.get("telegram_chat_id")
        if not chat_id:
            db = SessionLocal()
            try:
                prefs = PreferencesRepository(db).get_for_user(message.user_id)
                chat_id = prefs.telegram_chat_id if prefs else None
            finally:
                db.close()
        if not chat_id:
            return DeliveryResult(
                channel=self.name,
                status="skipped",
                error="telegram_chat_id missing",
            )

        url = (
            f"https://api.telegram.org/bot{settings.NOTIFY_TELEGRAM_BOT_TOKEN}/sendMessage"
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": format_text(message),
                        "disable_web_page_preview": True,
                    },
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
