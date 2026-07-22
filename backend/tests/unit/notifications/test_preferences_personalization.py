"""Unit tests for preference scoring / personalization."""

from __future__ import annotations

from app.personalization.scoring import score_message
from app.personalization.scoring import should_notify_by_score


def test_ignored_symbol_lowers_score() -> None:
    base = {
        "symbol": "EURUSD",
        "message_type": "Trade Signal",
        "priority": "Medium",
    }
    preferred = score_message(
        base,
        preferred_assets=["EURUSD"],
        ignored_symbols=[],
    )
    ignored = score_message(
        base,
        preferred_assets=[],
        ignored_symbols=["EURUSD"],
    )
    assert preferred > ignored
    assert should_notify_by_score(preferred, frequency="normal") is True
    assert should_notify_by_score(ignored, frequency="normal") is False


def test_soft_weights_and_frequency() -> None:
    msg = {"symbol": "XAUUSD", "message_type": "Breaking News"}
    boosted = score_message(
        msg,
        soft_weights={"message_types": {"Breaking News": 0.3}, "symbols": {"XAUUSD": 0.2}},
    )
    assert boosted >= 0.7
    assert should_notify_by_score(0.5, frequency="low") is False
    assert should_notify_by_score(0.5, frequency="high") is True
