"""
Configurable weighted technical score (0-100). Independent of confluence_engine.
"""

from __future__ import annotations

from typing import Any

from app.core.settings import settings


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(v)) for v in weights.values())
    if total <= 0:
        keys = ("trend", "momentum", "volatility", "volume", "structure")
        return {k: 100.0 / len(keys) for k in keys}
    return {k: (max(0.0, float(v)) / total) * 100.0 for k, v in weights.items()}


def _trend_component(snapshot: dict[str, Any]) -> float:
    alignment = snapshot.get("ema_alignment")
    strength = float(snapshot.get("trend_strength") or 0.0)
    if alignment == "Bullish":
        return _clamp(50.0 + strength / 2.0)
    if alignment == "Bearish":
        return _clamp(50.0 - strength / 2.0)
    return 50.0


def _momentum_component(snapshot: dict[str, Any]) -> float:
    rsi = snapshot.get("rsi")
    momentum = snapshot.get("momentum")
    indicators = snapshot.get("indicators") or {}
    hist = indicators.get("macd_histogram")

    score = 50.0
    if rsi is not None:
        score += (float(rsi) - 50.0) * 0.6
    if hist is not None:
        # Scale small histogram into +/- 15
        score += max(-15.0, min(15.0, float(hist) * 1000.0))
    if momentum == "Strong":
        score += 8.0
    elif momentum == "Weak":
        score -= 8.0
    return _clamp(score)


def _volatility_component(snapshot: dict[str, Any]) -> float:
    atr = snapshot.get("atr")
    if atr == "High":
        return 40.0  # elevated risk → slightly lower technical comfort
    if atr == "Low":
        return 65.0
    if atr == "Normal":
        return 55.0
    return 50.0


def _volume_component(snapshot: dict[str, Any]) -> float:
    volume = snapshot.get("volume")
    indicators = snapshot.get("indicators") or {}
    ratio = indicators.get("volume_ratio")
    score = 50.0
    if volume == "Increasing":
        score += 15.0
    elif volume == "Decreasing":
        score -= 10.0
    if ratio is not None:
        score += max(-15.0, min(15.0, (float(ratio) - 1.0) * 20.0))
    # Align volume with trend direction
    alignment = snapshot.get("ema_alignment")
    if alignment == "Bearish" and volume == "Increasing":
        score = 100.0 - score
    return _clamp(score)


def _structure_component(snapshot: dict[str, Any]) -> float:
    support = snapshot.get("support")
    resistance = snapshot.get("resistance")
    close = snapshot.get("price")
    if support is None or resistance is None or close is None:
        return 50.0
    span = float(resistance) - float(support)
    if span <= 0:
        return 50.0
    position = (float(close) - float(support)) / span
    return _clamp(position * 100.0)


_COMPONENT_FNS = {
    "trend": _trend_component,
    "momentum": _momentum_component,
    "volatility": _volatility_component,
    "volume": _volume_component,
    "structure": _structure_component,
}


def score_technical(
    snapshot: dict[str, Any],
    weights: dict[str, float] | None = None,
) -> float:
    """
    Weighted technical score in [0, 100].
    """
    resolved = _normalize_weights(weights or settings.TECHNICAL_SCORE_WEIGHTS)
    total = 0.0
    for name, weight in resolved.items():
        fn = _COMPONENT_FNS.get(name)
        if fn is None:
            continue
        total += fn(snapshot) * (weight / 100.0)
    return round(_clamp(total), 2)
