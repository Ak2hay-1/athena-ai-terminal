"""Tests for AI cache key stability."""

from __future__ import annotations

from app.ai.cache.keys import build_cache_key
from app.ai.cache.keys import canonical_json


def test_canonical_json_sorts_keys():
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_cache_key_is_stable_for_same_state():
    state = {
        "symbol": "XAUUSD",
        "timeframe": "1H",
        "trend": "Bullish",
        "confidence": 88,
    }
    key_a = build_cache_key("trade_explanation", state)
    key_b = build_cache_key("trade_explanation", dict(reversed(list(state.items()))))
    assert key_a == key_b
    assert key_a.startswith("ai:trade_explanation:")
    assert len(key_a.split(":")[-1]) == 64


def test_cache_key_changes_when_state_changes():
    base = {"symbol": "XAUUSD", "confidence": 88}
    other = {"symbol": "XAUUSD", "confidence": 87}
    assert build_cache_key("trade_explanation", base) != build_cache_key(
        "trade_explanation",
        other,
    )
