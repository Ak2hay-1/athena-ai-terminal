"""Deterministic market regime classification (no LLM)."""

from __future__ import annotations

from typing import Any


REGIMES = (
    "TRENDING",
    "RANGING",
    "HIGH_VOLATILITY",
    "LOW_VOLATILITY",
    "NEWS_DRIVEN",
    "BREAKOUT",
    "REVERSAL",
)


def classify_regime(
    *,
    analysis: dict[str, Any] | None = None,
    trend: str | None = None,
    news_blocked: bool = False,
    news_score: float | None = None,
    atr: float | None = None,
    atr_baseline: float | None = None,
    bos_active: bool = False,
    choch_active: bool = False,
) -> str:
    """
    Classify market regime from frozen Athena context.

    Priority order is intentional and reproducible.
    """
    analysis = analysis or {}
    volatility = analysis.get("volatility") or {}
    structure = analysis.get("market_structure") or analysis.get("structure") or {}
    news = analysis.get("news") or {}

    if news_blocked or bool(news.get("blocked")) or bool(news.get("high_impact")):
        return "NEWS_DRIVEN"

    if news_score is not None and abs(float(news_score)) >= 0.7:
        return "NEWS_DRIVEN"

    atr_val = atr
    if atr_val is None:
        atr_val = volatility.get("atr") or volatility.get("atr_value")
    baseline = atr_baseline
    if baseline is None:
        baseline = volatility.get("atr_baseline") or volatility.get("avg_atr")

    if atr_val is not None and baseline is not None and float(baseline) > 0:
        ratio = float(atr_val) / float(baseline)
        if ratio >= 1.5:
            return "HIGH_VOLATILITY"
        if ratio <= 0.6:
            return "LOW_VOLATILITY"

    bos = bos_active or bool(structure.get("bos")) or bool(analysis.get("bos"))
    choch = choch_active or bool(structure.get("choch")) or bool(analysis.get("choch"))

    if choch and not bos:
        return "REVERSAL"
    if bos and (trend or "").upper() in {"BULLISH", "BEARISH"}:
        return "BREAKOUT"

    trend_u = (trend or analysis.get("trend") or "").upper()
    if trend_u in {"BULLISH", "BEARISH"}:
        return "TRENDING"
    if trend_u in {"SIDEWAYS", "RANGING", "NEUTRAL"}:
        return "RANGING"

    return "RANGING"
