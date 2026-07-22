"""
SMC evidence score 0-100 (independent of confluence_engine).
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


def _structure_score(structure: dict[str, Any]) -> float:
    score = 40.0
    trend = structure.get("trend")
    if trend == "BULLISH" or trend == "BEARISH":
        score += 15.0
    bos = structure.get("bos") or {}
    if bos.get("present"):
        score += 15.0
        if bos.get("kind") == "external":
            score += 10.0
    if (structure.get("choch") or {}).get("present"):
        score += 10.0
    if structure.get("hh") and structure.get("hl"):
        score += 10.0
    if structure.get("lh") and structure.get("ll"):
        score += 10.0
    return _clamp(score)


def _liquidity_score(liquidity: dict[str, Any]) -> float:
    score = 35.0
    if liquidity.get("equal_highs") or liquidity.get("equal_lows"):
        score += 15.0
    if liquidity.get("liquidity_sweep"):
        score += 20.0
    if liquidity.get("stop_hunts"):
        score += 15.0
    if liquidity.get("inducement"):
        score += 10.0
    return _clamp(score)


def _ob_score(order_blocks: dict[str, Any]) -> float:
    score = 30.0
    active = int(order_blocks.get("active_count") or 0)
    score += min(25.0, active * 5.0)
    if order_blocks.get("demand_zones"):
        score += 15.0
    if order_blocks.get("supply_zones"):
        score += 15.0
    if order_blocks.get("breaker_blocks"):
        score += 10.0
    if order_blocks.get("mitigation_blocks"):
        score += 5.0
    return _clamp(score)


def _fvg_score(fvg: dict[str, Any]) -> float:
    score = 35.0
    gaps = int(fvg.get("bullish_count") or 0) + int(fvg.get("bearish_count") or 0)
    score += min(30.0, gaps * 5.0)
    if fvg.get("volume_imbalance"):
        score += 15.0
    if fvg.get("inverse_fvg"):
        score += 10.0
    return _clamp(score)


def _premium_score(premium: bool, discount: bool, percent: float | None) -> float:
    if discount:
        return 75.0 if percent is not None and percent < 40 else 65.0
    if premium:
        return 40.0 if percent is not None and percent > 60 else 50.0
    return 55.0


def score_smc(
    *,
    structure: dict[str, Any],
    liquidity: dict[str, Any],
    order_blocks: dict[str, Any],
    fvg: dict[str, Any],
    premium: bool,
    discount: bool,
    premium_percent: float | None,
    weights: dict[str, float] | None = None,
) -> float:
    resolved = _normalize_weights(weights or settings.SMC_SCORE_WEIGHTS)
    components = {
        "structure": _structure_score(structure),
        "liquidity": _liquidity_score(liquidity),
        "order_blocks": _ob_score(order_blocks),
        "fvg": _fvg_score(fvg),
        "premium_discount": _premium_score(premium, discount, premium_percent),
    }
    total = 0.0
    for key, weight in resolved.items():
        total += components.get(key, 50.0) * (weight / 100.0)
    return round(_clamp(total), 2)
