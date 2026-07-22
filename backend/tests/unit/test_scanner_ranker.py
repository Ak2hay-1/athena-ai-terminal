"""Unit tests for scanner ranker."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from app.services.scanner_ranker import display_signal
from app.services.scanner_ranker import rank_opportunity
from app.services.scanner_ranker import session_label


def test_display_signal_strong_threshold() -> None:
    assert display_signal("BUY", 80) == "STRONG_BUY"
    assert display_signal("BUY", 70) == "BUY"
    assert display_signal("SELL", 90) == "STRONG_SELL"
    assert display_signal("HOLD", 99) == "HOLD"


def test_rank_boosts_aligned_momentum_and_freshness() -> None:
    now = datetime(2024, 6, 3, 13, 0, tzinfo=timezone.utc)  # Overlap
    score, breakdown, stale, reasons = rank_opportunity(
        signal="BUY",
        confidence=70,
        trade_quality=80,
        trade_probability=70,
        confluence=60,
        change_percent=1.2,
        updated_at=now - timedelta(minutes=2),
        now=now,
        market_watch_change="breakout",
        market_watch_weight=12.0,
        session="Overlap",
    )
    assert not stale
    assert score >= 70
    assert breakdown.momentum_align > 0
    assert breakdown.market_watch > 0
    assert breakdown.freshness > 0
    assert any("breakout" in r for r in reasons)


def test_rank_penalizes_hold_and_stale() -> None:
    now = datetime(2024, 6, 3, 13, 0, tzinfo=timezone.utc)
    score, breakdown, stale, reasons = rank_opportunity(
        signal="HOLD",
        confidence=80,
        change_percent=0.5,
        updated_at=now - timedelta(hours=3),
        now=now,
        stale_threshold_minutes=45,
        session="Overlap",
    )
    assert stale
    assert breakdown.penalties < 0
    assert breakdown.freshness < 0
    assert score < 80
    assert "stale" in reasons or "standby" in reasons


def test_rank_no_trade_heavy_penalty() -> None:
    now = datetime(2024, 6, 3, 13, 0, tzinfo=timezone.utc)
    score, _, _, reasons = rank_opportunity(
        signal="NO_TRADE",
        confidence=90,
        updated_at=now,
        now=now,
    )
    assert score <= 60
    assert any("no trade" in r for r in reasons)


def test_session_label_overlap() -> None:
    assert session_label(datetime(2024, 1, 2, 13, 0, tzinfo=timezone.utc)) == "Overlap"
    assert session_label(datetime(2024, 1, 2, 8, 0, tzinfo=timezone.utc)) == "London"
