"""
Relevance scoring helpers for notifications.
"""

from __future__ import annotations

from typing import Any


def score_message(
    message: dict[str, Any],
    *,
    preferred_assets: list[str] | None = None,
    ignored_symbols: list[str] | None = None,
    preferred_rr: float | None = None,
    preferred_sessions: list[str] | None = None,
    soft_weights: dict[str, Any] | None = None,
) -> float:
    """
    Return relevance score in [0, 1]. Higher = more relevant.
    """
    score = 0.55
    symbol = str(message.get("symbol") or "").upper()
    message_type = str(message.get("message_type") or message.get("type") or "")
    preferred = {s.upper() for s in (preferred_assets or [])}
    ignored = {s.upper() for s in (ignored_symbols or [])}

    if symbol and symbol in ignored:
        score -= 0.45
    if symbol and symbol in preferred:
        score += 0.2

    rr = message.get("risk_reward") or message.get("rr")
    if preferred_rr is not None and rr is not None:
        try:
            if float(rr) >= float(preferred_rr):
                score += 0.1
            else:
                score -= 0.05
        except (TypeError, ValueError):
            pass

    session = str(message.get("session") or "").lower()
    prefsessions = {s.lower() for s in (preferred_sessions or [])}
    if session and prefsessions and session in prefsessions:
        score += 0.1

    weights = soft_weights or {}
    type_weight = weights.get("message_types") or {}
    if message_type in type_weight:
        try:
            score += float(type_weight[message_type])
        except (TypeError, ValueError):
            pass
    symbol_weight = weights.get("symbols") or {}
    if symbol in symbol_weight:
        try:
            score += float(symbol_weight[symbol])
        except (TypeError, ValueError):
            pass

    return max(0.0, min(1.0, score))


def should_notify_by_score(score: float, *, frequency: str = "normal") -> bool:
    thresholds = {
        "low": 0.7,
        "normal": 0.45,
        "high": 0.25,
    }
    return score >= thresholds.get(frequency.lower(), 0.45)
