"""Unit tests for new technical indicators."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.agents.technical.indicators import calculate_all
from app.agents.technical.indicators import latest_indicator_values
from app.indicators.adx import adx_indicator
from app.indicators.ichimoku import ichimoku_indicator
from app.indicators.sma import sma_indicator
from app.indicators.stochastic_rsi import stochastic_rsi_indicator
from app.indicators.volume_ma import volume_ma_indicator


def _synthetic_ohlcv(n: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    close = 100 + np.cumsum(rng.normal(0, 0.3, size=n))
    high = close + rng.uniform(0.1, 0.5, size=n)
    low = close - rng.uniform(0.1, 0.5, size=n)
    open_ = close + rng.normal(0, 0.1, size=n)
    volume = rng.integers(100, 1000, size=n)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": volume,
        }
    )


def test_sma_columns() -> None:
    df = sma_indicator.calculate(_synthetic_ohlcv())
    assert "sma_20" in df.columns
    assert abs(float(df["sma_20"].iloc[-1]) - float(df["close"].iloc[-20:].mean())) < 1e-9


def test_adx_range() -> None:
    df = adx_indicator.calculate(_synthetic_ohlcv())
    value = df["adx_14"].dropna().iloc[-1]
    assert 0 <= float(value) <= 100
    assert "plus_di_14" in df.columns
    assert "minus_di_14" in df.columns


def test_stochastic_rsi_bounds() -> None:
    df = stochastic_rsi_indicator.calculate(_synthetic_ohlcv())
    k = df["stoch_rsi_k"].dropna().iloc[-1]
    d = df["stoch_rsi_d"].dropna().iloc[-1]
    assert 0 <= float(k) <= 100
    assert 0 <= float(d) <= 100


def test_ichimoku_columns() -> None:
    df = ichimoku_indicator.calculate(_synthetic_ohlcv(200))
    for col in (
        "ichimoku_tenkan",
        "ichimoku_kijun",
        "ichimoku_senkou_a",
        "ichimoku_senkou_b",
    ):
        assert col in df.columns
        assert df[col].notna().any()


def test_volume_ma_ratio() -> None:
    df = volume_ma_indicator.calculate(_synthetic_ohlcv())
    assert "volume_ma_20" in df.columns
    assert "volume_ratio" in df.columns
    last = df.iloc[-1]
    expected = float(last["tick_volume"]) / float(last["volume_ma_20"])
    assert abs(float(last["volume_ratio"]) - expected) < 1e-9


def test_calculate_all_bundle() -> None:
    df = calculate_all(_synthetic_ohlcv(200))
    values = latest_indicator_values(df)
    assert values["rsi_14"] is not None
    assert values["atr_14"] is not None
    assert values["sma_20"] is not None
    assert values["adx_14"] is not None
    assert values["vwap"] is not None
