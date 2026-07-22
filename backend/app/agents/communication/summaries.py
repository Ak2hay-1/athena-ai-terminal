"""
Smart summary schedules: morning / evening / weekly / monthly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.agents.communication.composer import compose_from_event
from app.database.database import SessionLocal
from app.notifications.message import NotificationMessage
from app.repositories.preferences_repository import PreferencesRepository


def due_summaries_for_user(
    user_id: int,
    *,
    last_sent: dict[str, str],
) -> list[NotificationMessage]:
    """
    Return summary messages that are due now for the user timezone.
    last_sent maps summary_key -> YYYY-MM-DD (or YYYY-WW / YYYY-MM).
    """
    db = SessionLocal()
    try:
        prefs = PreferencesRepository(db).get_or_create(user_id)
        tz_name = prefs.timezone or "UTC"
    finally:
        db.close()

    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.now(tz)
    messages: list[NotificationMessage] = []

    # Morning brief 07:00–08:00
    morning_key = f"morning:{now.date().isoformat()}"
    if 7 <= now.hour < 8 and last_sent.get("morning") != now.date().isoformat():
        messages.append(
            _summary_message(
                user_id,
                "Daily Summary",
                "Morning Brief",
                f"Morning brief for {now.date().isoformat()}: review watchlist and overnight risk.",
                morning_key,
            )
        )
        last_sent["morning"] = now.date().isoformat()

    # Evening recap 20:00–21:00
    if 20 <= now.hour < 21 and last_sent.get("evening") != now.date().isoformat():
        messages.append(
            _summary_message(
                user_id,
                "Daily Summary",
                "Evening Recap",
                f"Evening recap for {now.date().isoformat()}: review closed trades and tomorrow bias.",
                f"evening:{now.date().isoformat()}",
            )
        )
        last_sent["evening"] = now.date().isoformat()

    iso = now.isocalendar()
    week_token = f"{iso.year}-W{iso.week:02d}"
    if now.weekday() == 6 and 18 <= now.hour < 19 and last_sent.get("weekly") != week_token:
        messages.append(
            _summary_message(
                user_id,
                "Weekly Summary",
                "Weekly Review",
                f"Weekly review {week_token}: win rate, RR, and session performance.",
                f"weekly:{week_token}",
            )
        )
        last_sent["weekly"] = week_token

    month_token = f"{now.year}-{now.month:02d}"
    if now.day == 1 and 9 <= now.hour < 10 and last_sent.get("monthly") != month_token:
        messages.append(
            _summary_message(
                user_id,
                "Monthly Report",
                "Monthly Performance",
                f"Monthly performance {month_token}: equity curve and drawdown summary.",
                f"monthly:{month_token}",
            )
        )
        last_sent["monthly"] = month_token

    return messages


def _summary_message(
    user_id: int,
    message_type: str,
    title: str,
    summary: str,
    dedupe_key: str,
) -> NotificationMessage:
    return NotificationMessage(
        user_id=user_id,
        message_type=message_type,
        priority="Low",
        summary=summary,
        confidence=None,
        reasoning=[title],
        risk="Low",
        evidence=[title],
        action="Open Athena dashboard for full report.",
        dedupe_key=dedupe_key,
        extra={"summary_kind": title},
    )


def portfolio_summary_message(user_id: int, portfolio_payload: dict[str, Any]) -> NotificationMessage:
    return compose_from_event(
        "PortfolioUpdated",
        portfolio_payload,
        user_id=user_id,
    )
