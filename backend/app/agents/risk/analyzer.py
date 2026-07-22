"""
Risk market-state analyzer — session, weekend, news, spread, volatility.
"""

from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timezone
from typing import Any

from app.core.settings import settings

# Approximate FX session windows (UTC hours)
_SESSION_WINDOWS: dict[str, tuple[int, int]] = {
    "asia": (0, 9),
    "london": (7, 16),
    "new_york": (12, 21),
}

# Fixed UTC holiday stubs (common market closures)
_HOLIDAYS = {
    (1, 1),
    (12, 25),
    (12, 26),
}

_CORRELATED_CLUSTERS = (
    {"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"},
    {"USDJPY", "EURJPY", "GBPJPY"},
    {"XAUUSD", "XAGUSD"},
)


def _active_sessions(now: datetime) -> list[str]:
    hour = now.astimezone(timezone.utc).hour
    return [
        name
        for name, (start, end) in _SESSION_WINDOWS.items()
        if start <= hour < end
    ]


def _is_holiday(day: date) -> bool:
    return (day.month, day.day) in _HOLIDAYS


def _correlation_risk(symbol: str) -> bool:
    name = symbol.upper()
    for cluster in _CORRELATED_CLUSTERS:
        if name in cluster and len(cluster) > 1:
            return True
    return False


def analyze_market_state(
    *,
    symbol: str,
    candle: dict[str, Any] | None,
    atr_ratio: float,
    news_context: dict[str, Any] | None,
    geometry: dict[str, Any],
    smc: dict[str, Any],
) -> dict[str, Any]:
    """
    Assemble warnings and market-state flags for risk scoring.
    """
    now = datetime.now(timezone.utc)
    sessions = _active_sessions(now)
    weekend = now.weekday() >= 5
    holiday = _is_holiday(now.date())
    news_risk = bool((news_context or {}).get("high_impact_upcoming"))

    spread = None
    if candle and candle.get("spread") is not None:
        try:
            spread = float(candle["spread"])
        except (TypeError, ValueError):
            spread = None

    high_spread = (
        spread is not None and spread >= float(settings.RISK_MAX_SPREAD_POINTS)
    )
    extreme_atr = atr_ratio >= float(settings.RISK_EXTREME_ATR_RATIO)
    low_liquidity = len(sessions) == 0 or (
        "asia" in sessions and "london" not in sessions and "new_york" not in sessions
        and now.hour in {21, 22, 23}
    )
    session_dead_zone = len(sessions) == 0
    poor_rr = float(geometry.get("risk_reward") or 0) < float(settings.VALIDATION_MIN_RR)
    correlation_risk = _correlation_risk(symbol)

    # Low liquidity also if SMC shows no pools and volume weak
    liquidity = smc.get("liquidity") or {}
    if not liquidity.get("liquidity_pools") and not liquidity.get("equal_highs"):
        if atr_ratio < 0.6:
            low_liquidity = True

    warnings: list[str] = []
    if weekend:
        warnings.append("weekend")
    if holiday:
        warnings.append("holiday")
    if low_liquidity:
        warnings.append("low_liquidity")
    if extreme_atr:
        warnings.append("extreme_atr")
    if high_spread:
        warnings.append("high_spread")
    if news_risk:
        warnings.append("news_risk")
    if poor_rr:
        warnings.append("poor_rr")
    if session_dead_zone:
        warnings.append("session_dead_zone")
    if correlation_risk:
        warnings.append("correlation_risk")

    volatility = "high" if extreme_atr else ("low" if atr_ratio < 0.7 else "normal")

    return {
        "sessions": sessions,
        "weekend": weekend,
        "holiday": holiday,
        "news_risk": news_risk,
        "spread": spread,
        "high_spread": high_spread,
        "volatility": volatility,
        "atr_ratio": atr_ratio,
        "low_liquidity": low_liquidity,
        "session_dead_zone": session_dead_zone,
        "correlation_risk": correlation_risk,
        "warnings": warnings,
        "news_score": (news_context or {}).get("score"),
    }
