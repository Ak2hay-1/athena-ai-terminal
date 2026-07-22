"""
Dedup, grouping, and quiet-hours helpers.
"""

from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.settings import settings
from app.notifications.message import NotificationMessage


class NotificationThrottle:
    def __init__(self) -> None:
        self._recent: dict[str, float] = {}
        self._groups: dict[str, float] = {}

    def dedupe_key(self, message: NotificationMessage) -> str:
        if message.dedupe_key:
            return message.dedupe_key
        return (
            f"{message.user_id}:{message.message_type}:"
            f"{message.symbol or '-'}:{message.side or '-'}"
        )

    def is_duplicate(self, message: NotificationMessage) -> bool:
        key = f"{message.user_id}:{self.dedupe_key(message)}"
        now = time.monotonic()
        ttl = max(30, int(settings.COMM_DEDUP_TTL_SECONDS))
        last = self._recent.get(key)
        if last is not None and now - last < ttl:
            return True
        self._recent[key] = now
        if len(self._recent) > 5000:
            cutoff = now - ttl
            self._recent = {k: v for k, v in self._recent.items() if v >= cutoff}
        return False

    def in_quiet_hours(
        self,
        *,
        timezone_name: str,
        quiet_start: str,
        quiet_end: str,
        priority: str,
    ) -> bool:
        if str(priority).lower() == "critical":
            return False
        try:
            tz = ZoneInfo(timezone_name or "UTC")
        except Exception:
            tz = ZoneInfo("UTC")
        now = datetime.now(tz)
        start = _parse_hhmm(quiet_start or settings.COMM_DEFAULT_QUIET_START)
        end = _parse_hhmm(quiet_end or settings.COMM_DEFAULT_QUIET_END)
        minutes = now.hour * 60 + now.minute
        if start == end:
            return False
        if start < end:
            return start <= minutes < end
        return minutes >= start or minutes < end

    def group_key(self, message: NotificationMessage) -> str:
        return f"{message.user_id}:{message.message_type}:{message.symbol or 'ALL'}"

    def maybe_group(self, message: NotificationMessage) -> NotificationMessage | None:
        """
        Allow first alert in a group window; suppress similar follow-ups.
        Critical/High always pass.
        """
        if str(message.priority).lower() in {"critical", "high"}:
            return message

        key = self.group_key(message)
        now = time.monotonic()
        window = max(5, int(settings.COMM_GROUP_WINDOW_SECONDS))
        last = self._groups.get(key)
        if last is not None and now - last < window:
            return None
        self._groups[key] = now
        if len(self._groups) > 5000:
            cutoff = now - window
            self._groups = {k: v for k, v in self._groups.items() if v >= cutoff}
        return message


def _parse_hhmm(value: str) -> int:
    parts = str(value or "00:00").split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    return hour * 60 + minute


throttle = NotificationThrottle()
