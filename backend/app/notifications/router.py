"""
Notification router — channel selection, persistence, fan-out.
"""

from __future__ import annotations

from typing import Any

from app.core.logger import get_logger
from app.core.settings import settings
from app.database.database import SessionLocal
from app.models.notification import NotificationDelivery
from app.notifications.discord import DiscordChannel
from app.notifications.email import EmailChannel
from app.notifications.message import DeliveryResult
from app.notifications.message import NotificationMessage
from app.notifications.push import PushChannel
from app.notifications.telegram import TelegramChannel
from app.notifications.throttle import throttle
from app.notifications.websocket import WebSocketChannel
from app.repositories.notification_repository import NotificationRepository
from app.repositories.preferences_repository import PreferencesRepository

logger = get_logger("athena.notifications.router")


class NotificationRouter:
    def __init__(self) -> None:
        self._channels = {
            "telegram": TelegramChannel(),
            "discord": DiscordChannel(),
            "email": EmailChannel(),
            "push": PushChannel(),
            "websocket": WebSocketChannel(),
        }
        self.sent = 0
        self.failed = 0
        self.skipped = 0

    def select_channels(
        self,
        *,
        preferred_channel: str | None,
        priority: str,
    ) -> list[str]:
        preferred = (preferred_channel or "websocket").lower()
        channels = [preferred]
        if preferred != "websocket" and settings.NOTIFY_WEBSOCKET_ENABLED:
            channels.append("websocket")
        if str(priority).lower() == "critical":
            for name in ("telegram", "email", "discord"):
                if name not in channels:
                    channels.append(name)
        return channels

    async def dispatch(
        self,
        message: NotificationMessage,
        *,
        respect_quiet_hours: bool = True,
    ) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            prefs = PreferencesRepository(db).get_or_create(message.user_id)
            quiet_start = prefs.quiet_hours_start
            quiet_end = prefs.quiet_hours_end
            tz_name = prefs.timezone or "UTC"
            preferred = prefs.preferred_channel
        finally:
            db.close()

        if throttle.is_duplicate(message):
            self.skipped += 1
            return [{"channel": "all", "status": "skipped", "error": "dedupe"}]

        if respect_quiet_hours and throttle.in_quiet_hours(
            timezone_name=tz_name,
            quiet_start=quiet_start,
            quiet_end=quiet_end,
            priority=message.priority,
        ):
            self.skipped += 1
            return [{"channel": "all", "status": "skipped", "error": "quiet_hours"}]

        grouped = throttle.maybe_group(message)
        if grouped is None:
            self.skipped += 1
            return [{"channel": "all", "status": "skipped", "error": "grouped_buffer"}]
        message = grouped

        channel_names = self.select_channels(
            preferred_channel=message.channel_hint or preferred,
            priority=message.priority,
        )
        results: list[dict[str, Any]] = []
        for name in channel_names:
            channel = self._channels.get(name)
            if channel is None:
                continue
            result = await channel.send(message)
            self._record(message, result)
            results.append(
                {
                    "channel": result.channel,
                    "status": result.status,
                    "latency_ms": result.latency_ms,
                    "error": result.error,
                }
            )
            if result.status == "sent":
                self.sent += 1
            elif result.status == "failed":
                self.failed += 1
            else:
                self.skipped += 1
        return results

    def _record(self, message: NotificationMessage, result: DeliveryResult) -> None:
        db = SessionLocal()
        try:
            row = NotificationDelivery(
                user_id=message.user_id,
                channel=result.channel,
                message_type=message.message_type,
                priority=message.priority,
                payload=message.to_dict(),
                status=result.status,
                latency_ms=result.latency_ms,
                error=result.error,
                dedupe_key=throttle.dedupe_key(message),
            )
            NotificationRepository(db).create(row)
            db.commit()
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.warning("notification persist failed: %s", exc)
        finally:
            db.close()


notification_router = NotificationRouter()
