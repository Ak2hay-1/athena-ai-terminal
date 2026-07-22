"""
Risk score 0-100 (higher = safer). Evidence only.
"""

from __future__ import annotations

from typing import Any

from app.core.settings import settings


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(v)) for v in weights.values())
    if total <= 0:
        return {k: 20.0 for k in weights}
    return {k: (max(0.0, float(v)) / total) * 100.0 for k, v in weights.items()}


def score_risk(
    *,
    geometry: dict[str, Any],
    market_state: dict[str, Any],
    weights: dict[str, float] | None = None,
) -> float:
    resolved = _normalize_weights(weights or settings.RISK_SCORE_WEIGHTS)

    rr = float(geometry.get("risk_reward") or 0)
    geometry_score = 40.0
    if rr >= float(settings.PREFERRED_RR):
        geometry_score = 90.0
    elif rr >= float(settings.MIN_RR):
        geometry_score = 70.0
    elif rr > 0:
        geometry_score = 40.0
    else:
        geometry_score = 10.0
    if not geometry.get("valid"):
        geometry_score = min(geometry_score, 25.0)

    atr_ratio = float(market_state.get("atr_ratio") or 1.0)
    if atr_ratio >= float(settings.RISK_EXTREME_ATR_RATIO):
        volatility_score = 25.0
    elif atr_ratio < 0.7:
        volatility_score = 70.0
    else:
        volatility_score = 80.0

    session_score = 80.0
    if market_state.get("weekend") or market_state.get("holiday"):
        session_score = 10.0
    elif market_state.get("session_dead_zone") or not market_state.get("sessions"):
        session_score = 35.0
    elif "london" in (market_state.get("sessions") or []) or "new_york" in (
        market_state.get("sessions") or []
    ):
        session_score = 90.0

    news_score = 20.0 if market_state.get("news_risk") else 90.0

    liquidity_score = 85.0
    if market_state.get("low_liquidity"):
        liquidity_score = 30.0
    if market_state.get("high_spread"):
        liquidity_score = min(liquidity_score, 35.0)

    components = {
        "geometry": geometry_score,
        "volatility": volatility_score,
        "session": session_score,
        "news": news_score,
        "liquidity": liquidity_score,
    }

    total = 0.0
    for key, weight in resolved.items():
        total += components.get(key, 50.0) * (weight / 100.0)
    return round(_clamp(total), 2)
