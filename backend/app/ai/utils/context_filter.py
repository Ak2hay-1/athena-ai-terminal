"""
Strip forbidden payloads before AI calls.

Never send OHLC candles, indicator history, order books, or raw chart data.
"""

from __future__ import annotations

from typing import Any

FORBIDDEN_KEYS = frozenset(
    {
        "ohlc",
        "candles",
        "candle_history",
        "historical_candles",
        "order_book",
        "orderbook",
        "bids",
        "asks",
        "indicator_history",
        "raw_chart",
        "dataframe",
        "bars",
        "tick_data",
        "ticks",
    }
)


def sanitize_payload(payload: Any) -> Any:
    """Recursively remove forbidden keys and large numeric series."""

    if isinstance(payload, dict):
        cleaned: dict[str, Any] = {}
        for key, value in payload.items():
            key_lower = str(key).lower()
            if key_lower in FORBIDDEN_KEYS:
                continue
            if key_lower.endswith("_history") or key_lower.endswith("_series"):
                continue
            if _is_ohlc_list(value):
                continue
            cleaned[key] = sanitize_payload(value)
        return cleaned

    if isinstance(payload, list):
        if _is_ohlc_list(payload):
            return []
        if len(payload) > 50 and all(isinstance(item, (int, float)) for item in payload):
            return []
        return [sanitize_payload(item) for item in payload]

    return payload


def _is_ohlc_list(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    first = value[0]
    if not isinstance(first, dict):
        return False
    keys = {str(k).lower() for k in first.keys()}
    return {"open", "high", "low", "close"}.issubset(keys)


def assert_safe_context(payload: dict[str, Any]) -> dict[str, Any]:
    """Sanitize and return a safe context dict."""

    return sanitize_payload(payload)
