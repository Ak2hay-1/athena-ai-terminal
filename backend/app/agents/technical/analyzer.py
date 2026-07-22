"""
Technical analysis snapshot builder (deterministic, no AI).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.agents.technical.indicators import calculate_all
from app.agents.technical.indicators import latest_indicator_values


def _ema_alignment(values: dict[str, float | None]) -> str:
    e9 = values.get("ema_9")
    e20 = values.get("ema_20")
    e50 = values.get("ema_50")
    if e9 is None or e20 is None or e50 is None:
        return "Neutral"
    if e9 > e20 > e50:
        return "Bullish"
    if e9 < e20 < e50:
        return "Bearish"
    return "Neutral"


def _trend_label(values: dict[str, float | None], alignment: str) -> str:
    adx = values.get("adx_14")
    if alignment == "Neutral":
        return "Sideways"
    if adx is not None and adx >= 25:
        return alignment
    return alignment


def _momentum_label(values: dict[str, float | None]) -> str:
    rsi = values.get("rsi_14")
    hist = values.get("macd_histogram")
    stoch_k = values.get("stoch_rsi_k")
    score = 0
    if rsi is not None:
        if rsi >= 60:
            score += 1
        elif rsi <= 40:
            score -= 1
    if hist is not None:
        if hist > 0:
            score += 1
        elif hist < 0:
            score -= 1
    if stoch_k is not None:
        if stoch_k >= 60:
            score += 1
        elif stoch_k <= 40:
            score -= 1
    if score >= 2:
        return "Strong"
    if score <= -2:
        return "Weak"
    return "Moderate"


def _atr_regime(df: pd.DataFrame, atr: float | None) -> str:
    if atr is None or "atr_14" not in df.columns:
        return "Unknown"
    series = df["atr_14"].dropna()
    if len(series) < 20:
        return "Unknown"
    mean = float(series.iloc[-20:].mean())
    if mean <= 0:
        return "Unknown"
    ratio = atr / mean
    if ratio >= 1.4:
        return "High"
    if ratio <= 0.7:
        return "Low"
    return "Normal"


def _volume_direction(values: dict[str, float | None]) -> str:
    ratio = values.get("volume_ratio")
    if ratio is None:
        return "Unknown"
    if ratio >= 1.2:
        return "Increasing"
    if ratio <= 0.8:
        return "Decreasing"
    return "Stable"


def _support_resistance(df: pd.DataFrame) -> tuple[float | None, float | None]:
    if df.empty:
        return None, None
    window = df.tail(50)
    support = float(window["low"].min())
    resistance = float(window["high"].max())
    return support, resistance


def _trend_strength(values: dict[str, float | None], alignment: str) -> float:
    adx = values.get("adx_14") or 0.0
    base = min(max(adx, 0.0), 100.0)
    if alignment == "Neutral":
        return round(base * 0.5, 2)
    return round(base, 2)


def analyze(dataframe: pd.DataFrame) -> dict[str, Any]:
    """
    Produce a structured technical snapshot from OHLCV data.
    """
    if dataframe.empty or len(dataframe) < 30:
        return {
            "trend": "Unknown",
            "momentum": "Unknown",
            "trend_strength": 0.0,
            "rsi": None,
            "atr": "Unknown",
            "volume": "Unknown",
            "ema_alignment": "Neutral",
            "support": None,
            "resistance": None,
            "indicators": {},
        }

    df = calculate_all(dataframe)
    values = latest_indicator_values(df)
    alignment = _ema_alignment(values)
    support, resistance = _support_resistance(df)
    atr_value = values.get("atr_14")
    close = float(df.iloc[-1]["close"])

    return {
        "trend": _trend_label(values, alignment),
        "momentum": _momentum_label(values),
        "trend_strength": _trend_strength(values, alignment),
        "rsi": values.get("rsi_14"),
        "atr": _atr_regime(df, atr_value),
        "volume": _volume_direction(values),
        "ema_alignment": alignment,
        "support": support,
        "resistance": resistance,
        "price": close,
        "indicators": values,
        "dataframe": df,
    }
