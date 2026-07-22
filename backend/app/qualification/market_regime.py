"""
Market regime detection for institutional strategy selection.

Classifies every symbol into TRENDING / RANGING / BREAKOUT / COMPRESSION /
EXPANSION / HIGH_VOLATILITY / LOW_VOLATILITY.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.settings import settings
from app.qualification.models import MarketRegime


# Strategies allowed per regime (RiskEngine / qualification use this).
REGIME_COMPATIBLE_STRATEGIES: dict[str, set[str]] = {
    MarketRegime.TRENDING.value: {"trend_continuation", "pullback", "breakout"},
    MarketRegime.BREAKOUT.value: {"breakout", "expansion"},
    MarketRegime.EXPANSION.value: {"trend_continuation", "breakout", "expansion"},
    MarketRegime.COMPRESSION.value: set(),  # no directional trade
    MarketRegime.RANGING.value: set(),  # breakout/trend disabled
    MarketRegime.HIGH_VOLATILITY.value: {"breakout", "expansion"},
    MarketRegime.LOW_VOLATILITY.value: set(),  # wait for expansion
}


def detect_regime(
    dataframe: pd.DataFrame,
    *,
    analysis: dict[str, Any] | None = None,
    trend: str | None = None,
    atr: float | None = None,
    atr_baseline: float | None = None,
    bos_active: bool = False,
    choch_active: bool = False,
) -> str:
    """
    Lightweight, deterministic regime classification from OHLCV + analysis hints.
    """
    analysis = analysis or {}
    volatility = analysis.get("volatility") or {}
    structure = analysis.get("market_structure") or analysis.get("structure") or {}

    atr_val = atr
    if atr_val is None and not dataframe.empty and "atr_14" in dataframe.columns:
        atr_val = float(dataframe["atr_14"].iloc[-1] or 0.0)
    if atr_val is None:
        atr_val = volatility.get("atr") or volatility.get("atr_value")

    baseline = atr_baseline
    if baseline is None:
        baseline = volatility.get("atr_baseline") or volatility.get("avg_atr")
    if baseline is None and not dataframe.empty and "atr_14" in dataframe.columns:
        series = dataframe["atr_14"].dropna().tail(50)
        if len(series) >= 10:
            baseline = float(series.mean())

    atr_ratio = None
    if atr_val is not None and baseline is not None and float(baseline) > 0:
        atr_ratio = float(atr_val) / float(baseline)

    # Compression: ATR collapsing + tight recent range
    if atr_ratio is not None and atr_ratio <= float(settings.QUAL_COMPRESSION_ATR_RATIO):
        if _range_compressed(dataframe):
            return MarketRegime.COMPRESSION.value
        return MarketRegime.LOW_VOLATILITY.value

    if atr_ratio is not None and atr_ratio >= float(settings.QUAL_EXPANSION_ATR_RATIO):
        if atr_ratio >= float(settings.QUAL_HIGH_VOL_ATR_RATIO):
            return MarketRegime.HIGH_VOLATILITY.value
        return MarketRegime.EXPANSION.value

    bos = bos_active or bool(structure.get("bos")) or bool(analysis.get("bos"))
    choch = choch_active or bool(structure.get("choch")) or bool(analysis.get("choch"))

    trend_u = _trend_label(trend, analysis, dataframe)

    if bos and trend_u in {"BULLISH", "BEARISH"}:
        return MarketRegime.BREAKOUT.value

    if choch and not bos:
        # Treat reversal / CHOCH as ranging until structure re-establishes
        return MarketRegime.RANGING.value

    if trend_u in {"BULLISH", "BEARISH"}:
        adx = _latest_adx(dataframe)
        if adx is not None and adx >= float(settings.QUAL_MIN_ADX):
            return MarketRegime.TRENDING.value
        return MarketRegime.RANGING.value

    return MarketRegime.RANGING.value


def regime_allows_directional_trade(regime: str) -> bool:
    """False for regimes where Athena must stand aside."""
    allowed = REGIME_COMPATIBLE_STRATEGIES.get((regime or "").upper(), set())
    return len(allowed) > 0


def strategy_compatible(regime: str, strategy: str) -> bool:
    allowed = REGIME_COMPATIBLE_STRATEGIES.get((regime or "").upper(), set())
    return strategy in allowed


def _trend_label(
    trend: str | None,
    analysis: dict[str, Any],
    dataframe: pd.DataFrame,
) -> str:
    if trend:
        return str(trend).upper()
    nested = analysis.get("trend")
    if isinstance(nested, dict):
        return str(nested.get("direction") or "SIDEWAYS").upper()
    if isinstance(nested, str):
        return nested.upper()
    if not dataframe.empty and "trend" in dataframe.columns:
        return str(dataframe["trend"].iloc[-1] or "SIDEWAYS").upper()
    return "SIDEWAYS"


def _latest_adx(dataframe: pd.DataFrame) -> float | None:
    if dataframe.empty:
        return None
    for col in ("adx_14", "adx"):
        if col in dataframe.columns:
            val = dataframe[col].iloc[-1]
            try:
                return float(val)
            except (TypeError, ValueError):
                return None
    return None


def _range_compressed(dataframe: pd.DataFrame, bars: int = 20) -> bool:
    if dataframe.empty or len(dataframe) < bars:
        return False
    window = dataframe.tail(bars)
    high = float(window["high"].max())
    low = float(window["low"].min())
    mid = (high + low) / 2.0
    if mid <= 0:
        return False
    width = (high - low) / mid
    return width <= float(settings.QUAL_COMPRESSION_RANGE_FRACTION)
