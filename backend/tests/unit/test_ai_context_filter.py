"""Tests for AI context sanitization."""

from __future__ import annotations

from app.ai.utils.context_filter import sanitize_payload


def test_strips_ohlc_candle_lists():
    payload = {
        "trend": "BULLISH",
        "candles": [
            {"open": 1, "high": 2, "low": 0.5, "close": 1.5},
            {"open": 1.5, "high": 2.5, "low": 1, "close": 2},
        ],
        "order_book": {"bids": [], "asks": []},
    }
    cleaned = sanitize_payload(payload)
    assert "candles" not in cleaned
    assert "order_book" not in cleaned
    assert cleaned["trend"] == "BULLISH"


def test_strips_indicator_history_keys():
    payload = {
        "rsi": 55,
        "rsi_history": [40, 45, 50, 55],
        "momentum": {"macd": 0.1},
    }
    cleaned = sanitize_payload(payload)
    assert "rsi_history" not in cleaned
    assert cleaned["rsi"] == 55
    assert cleaned["momentum"]["macd"] == 0.1


def test_strips_large_numeric_series():
    payload = {"series": list(range(100)), "ok": True}
    cleaned = sanitize_payload(payload)
    assert cleaned["series"] == []
    assert cleaned["ok"] is True
