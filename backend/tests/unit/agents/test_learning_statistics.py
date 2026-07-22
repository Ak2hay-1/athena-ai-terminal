"""Unit tests for learning statistics helpers."""

from __future__ import annotations

from app.agents.learning.statistics import best_worst_sessions
from app.agents.learning.statistics import repeated_patterns


def test_best_worst_sessions_and_patterns() -> None:
    outcomes = [
        {"session": ["london"], "outcome": "win", "symbol": "EURUSD", "timeframe": "M5", "status": "APPROVED"},
        {"session": ["london"], "outcome": "win", "symbol": "EURUSD", "timeframe": "M5", "status": "APPROVED"},
        {"session": ["london"], "outcome": "win", "symbol": "EURUSD", "timeframe": "M5", "status": "APPROVED"},
        {"session": ["asia"], "outcome": "loss", "symbol": "USDJPY", "timeframe": "M15", "status": "APPROVED"},
        {"session": ["asia"], "outcome": "loss", "symbol": "USDJPY", "timeframe": "M15", "status": "APPROVED"},
        {"session": ["asia"], "outcome": "loss", "symbol": "USDJPY", "timeframe": "M15", "status": "APPROVED"},
    ]
    best, worst = best_worst_sessions(outcomes)
    assert best[0]["session"] == "london"
    assert best[0]["win_rate"] == 100.0
    assert worst[0]["session"] == "asia"

    patterns = repeated_patterns(outcomes, min_count=3)
    assert patterns["repeated_winners"]
    assert patterns["repeated_failures"]
