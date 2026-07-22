"""Unit tests for technical scoring."""

from __future__ import annotations

from app.agents.technical.scorer import score_technical


def _bullish_snapshot() -> dict:
    return {
        "ema_alignment": "Bullish",
        "trend_strength": 80.0,
        "momentum": "Strong",
        "rsi": 65.0,
        "atr": "Normal",
        "volume": "Increasing",
        "support": 1.08,
        "resistance": 1.10,
        "price": 1.095,
        "indicators": {
            "macd_histogram": 0.001,
            "volume_ratio": 1.5,
        },
    }


def _bearish_snapshot() -> dict:
    return {
        "ema_alignment": "Bearish",
        "trend_strength": 80.0,
        "momentum": "Weak",
        "rsi": 35.0,
        "atr": "High",
        "volume": "Increasing",
        "support": 1.08,
        "resistance": 1.10,
        "price": 1.082,
        "indicators": {
            "macd_histogram": -0.001,
            "volume_ratio": 1.4,
        },
    }


def test_score_bounds() -> None:
    score = score_technical(_bullish_snapshot())
    assert 0.0 <= score <= 100.0


def test_bullish_scores_higher_than_bearish() -> None:
    bull = score_technical(_bullish_snapshot())
    bear = score_technical(_bearish_snapshot())
    assert bull > bear


def test_custom_weights_applied() -> None:
    snap = _bullish_snapshot()
    trend_heavy = score_technical(
        snap,
        weights={"trend": 100.0, "momentum": 0, "volatility": 0, "volume": 0, "structure": 0},
    )
    # Pure trend bullish with strength 80 → 50 + 40 = 90
    assert trend_heavy == 90.0
