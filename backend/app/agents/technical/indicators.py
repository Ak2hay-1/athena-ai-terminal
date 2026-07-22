"""
Technical agent indicator bundle.

Reuses existing indicator modules and adds agent-specific ones.
Does not modify the recommendation indicator_engine registry.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.adx import adx_indicator
from app.indicators.atr import atr_indicator
from app.indicators.bollinger import bollinger_indicator
from app.indicators.ichimoku import ichimoku_indicator
from app.indicators.macd import macd_indicator
from app.indicators.moving_average import moving_average_indicator
from app.indicators.rsi import rsi_indicator
from app.indicators.sma import sma_indicator
from app.indicators.stochastic_rsi import stochastic_rsi_indicator
from app.indicators.volume_ma import volume_ma_indicator
from app.indicators.vwap import VWAP

_vwap = VWAP()


def candles_to_dataframe(candles: list[dict]) -> pd.DataFrame:
    """Build an OHLCV DataFrame from serialized candle dicts."""
    if not candles:
        return pd.DataFrame(
            columns=["time", "open", "high", "low", "close", "tick_volume"]
        )
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    for col in ("open", "high", "low", "close"):
        df[col] = df[col].astype(float)
    df["tick_volume"] = df["tick_volume"].astype(float)
    df = df.sort_values("time").reset_index(drop=True)
    return df


def calculate_all(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full technical indicator set on a candle DataFrame.
    """
    if dataframe.empty:
        return dataframe.copy()

    df = dataframe.copy()
    df = moving_average_indicator.calculate(df)
    df = sma_indicator.calculate(df)
    df = rsi_indicator.calculate(df)
    df = macd_indicator.calculate(df)
    df = atr_indicator.calculate(df)
    df = bollinger_indicator.calculate(df)
    df = _vwap.calculate(df)
    df = stochastic_rsi_indicator.calculate(df)
    df = adx_indicator.calculate(df)
    df = ichimoku_indicator.calculate(df)
    df = volume_ma_indicator.calculate(df)
    return df


def latest_indicator_values(df: pd.DataFrame) -> dict[str, float | None]:
    """Extract the latest non-null indicator values as a plain dict."""
    if df.empty:
        return {}

    row = df.iloc[-1]
    keys = [
        "ema_9",
        "ema_20",
        "ema_50",
        "ema_100",
        "ema_200",
        "sma_9",
        "sma_20",
        "sma_50",
        "sma_200",
        "rsi_14",
        "macd",
        "macd_signal",
        "macd_histogram",
        "atr_14",
        "bb_middle",
        "bb_upper",
        "bb_lower",
        "bb_width",
        "vwap",
        "stoch_rsi_k",
        "stoch_rsi_d",
        "adx_14",
        "plus_di_14",
        "minus_di_14",
        "ichimoku_tenkan",
        "ichimoku_kijun",
        "ichimoku_senkou_a",
        "ichimoku_senkou_b",
        "volume_ma_20",
        "volume_ratio",
    ]
    values: dict[str, float | None] = {}
    for key in keys:
        if key not in df.columns:
            values[key] = None
            continue
        raw = row[key]
        if pd.isna(raw):
            values[key] = None
        else:
            values[key] = float(raw)
    return values
