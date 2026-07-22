"""
Email notification channel (SMTP).
"""

from __future__ import annotations

import asyncio
import smtplib
import time
from email.message import EmailMessage

from app.core.settings import settings
from app.database.database import SessionLocal
from app.models.user import User
from app.notifications.message import DeliveryResult
from app.notifications.message import NotificationMessage
from app.notifications.templates import format_subject
from app.notifications.templates import format_text
from app.repositories.preferences_repository import PreferencesRepository
from sqlalchemy import select


class EmailChannel:
    name = "email"

    async def send(self, message: NotificationMessage) -> DeliveryResult:
        started = time.perf_counter()
        if not settings.NOTIFY_EMAIL_ENABLED or not settings.NOTIFY_SMTP_HOST:
            return DeliveryResult(
                channel=self.name,
                status="skipped",
                error="email disabled or SMTP host missing",
            )

        to_addr = await asyncio.to_thread(self._resolve_email, message.user_id)
        if not to_addr:
            return DeliveryResult(
                channel=self.name,
                status="skipped",
                error="recipient email missing",
            )

        msg = EmailMessage()
        msg["Subject"] = format_subject(message)
        msg["From"] = settings.NOTIFY_SMTP_FROM or settings.NOTIFY_SMTP_USER
        msg["To"] = to_addr
        msg.set_content(format_text(message))

        try:
            await asyncio.to_thread(self._smtp_send, msg)
            return DeliveryResult(
                channel=self.name,
                status="sent",
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception as exc:  # noqa: BLE001
            return DeliveryResult(
                channel=self.name,
                status="failed",
                latency_ms=(time.perf_counter() - started) * 1000,
                error=str(exc),
            )

    def _resolve_email(self, user_id: int) -> str | None:
        db = SessionLocal()
        try:
            prefs = PreferencesRepository(db).get_for_user(user_id)
            if prefs and prefs.email_override:
                return prefs.email_override
            user = db.scalars(select(User).where(User.id == user_id)).first()
            return user.email if user else None
        finally:
            db.close()

    def _smtp_send(self, msg: EmailMessage) -> None:
        with smtplib.SMTP(settings.NOTIFY_SMTP_HOST, int(settings.NOTIFY_SMTP_PORT)) as smtp:
            smtp.starttls()
            if settings.NOTIFY_SMTP_USER:
                smtp.login(settings.NOTIFY_SMTP_USER, settings.NOTIFY_SMTP_PASSWORD)
            smtp.send_message(msg)
