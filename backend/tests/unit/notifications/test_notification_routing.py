"""Unit tests for notification throttle and channel selection."""

from __future__ import annotations

from app.notifications.message import NotificationMessage
from app.notifications.router import NotificationRouter
from app.notifications.throttle import NotificationThrottle


def _msg(**kwargs) -> NotificationMessage:
    base = dict(
        user_id=1,
        message_type="Trade Signal",
        priority="Medium",
        summary="test",
        symbol="EURUSD",
        side="BUY",
        dedupe_key="k1",
    )
    base.update(kwargs)
    return NotificationMessage(**base)


def test_dedupe_and_group_window() -> None:
    t = NotificationThrottle()
    m1 = _msg()
    assert t.is_duplicate(m1) is False
    assert t.is_duplicate(m1) is True

    t2 = NotificationThrottle()
    first = t2.maybe_group(_msg(priority="Medium", dedupe_key="g1"))
    second = t2.maybe_group(_msg(priority="Medium", dedupe_key="g2"))
    assert first is not None
    assert second is None  # same group key user/type/symbol
    critical = t2.maybe_group(_msg(priority="Critical", dedupe_key="g3"))
    assert critical is not None


def test_quiet_hours_skips_non_critical() -> None:
    t = NotificationThrottle()
    # Force a window that includes "now" by using full-day quiet hours
    assert (
        t.in_quiet_hours(
            timezone_name="UTC",
            quiet_start="00:00",
            quiet_end="23:59",
            priority="Medium",
        )
        is True
    )
    assert (
        t.in_quiet_hours(
            timezone_name="UTC",
            quiet_start="00:00",
            quiet_end="23:59",
            priority="Critical",
        )
        is False
    )


def test_channel_selection() -> None:
    router = NotificationRouter()
    channels = router.select_channels(preferred_channel="telegram", priority="Medium")
    assert channels[0] == "telegram"
    assert "websocket" in channels
    critical = router.select_channels(preferred_channel="websocket", priority="Critical")
    assert "telegram" in critical or "email" in critical
