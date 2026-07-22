"""Qualification engine unit tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.qualification.market_regime import detect_regime
from app.qualification.market_regime import regime_allows_directional_trade
from app.qualification.models import MarketRegime
from app.qualification.qualification_engine import QualificationEngine


def _ohlcv(n: int = 80, *, trend: str = "up", atr_scale: float = 1.0) -> pd.DataFrame:
    idx = pd.RangeIndex(n)
    base = 1.1000 + (np.arange(n) * (0.0008 if trend == "up" else -0.0008 if trend == "down" else 0.0))
    noise = np.sin(np.arange(n) / 5) * 0.00005 * atr_scale
    close = base + noise
    high = close + 0.0004 * atr_scale
    low = close - 0.0004 * atr_scale
    open_ = close - 0.00005
    atr = np.full(n, 0.00035 * atr_scale)
    adx = np.full(n, 28.0 if trend in {"up", "down"} else 12.0)
    vol = np.full(n, 200.0)
    vol[-1] = 260.0
    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": vol,
            "atr_14": atr,
            "adx_14": adx,
            "trend": ["BULLISH" if trend == "up" else "BEARISH" if trend == "down" else "SIDEWAYS"] * n,
            "bos": [False] * (n - 1) + [True],
            "choch": [False] * n,
        }
    )


def test_rejects_ranging_weak_adx():
    engine = QualificationEngine()
    df = _ohlcv(trend="flat")
    result = engine.evaluate(
        df,
        symbol="EURUSD",
        timeframe="M15",
        higher_timeframes={
            "H1": _ohlcv(trend="flat"),
            "H4": _ohlcv(trend="flat"),
        },
    )
    assert result.qualified is False
    assert any("Trend" in g.name or "Regime" in g.name for g in result.gates if not g.passed)


def test_rejects_low_atr():
    engine = QualificationEngine()
    df = _ohlcv(trend="up", atr_scale=0.01)
    df["atr_14"] = 1e-8
    result = engine.evaluate(
        df,
        symbol="EURUSD",
        timeframe="M15",
        higher_timeframes={
            "H1": _ohlcv(trend="up"),
            "H4": _ohlcv(trend="up"),
        },
    )
    assert result.qualified is False
    assert any(g.name == "ATR / Volatility" and not g.passed for g in result.gates)


def test_regime_compression_not_tradeable():
    df = _ohlcv(trend="flat", atr_scale=0.2)
    df["atr_14"] = 0.00005
    regime = detect_regime(df, trend="SIDEWAYS", atr=0.00005, atr_baseline=0.0004)
    assert regime in {
        MarketRegime.COMPRESSION.value,
        MarketRegime.LOW_VOLATILITY.value,
        MarketRegime.RANGING.value,
    }
    assert regime_allows_directional_trade(MarketRegime.COMPRESSION.value) is False
    assert regime_allows_directional_trade(MarketRegime.RANGING.value) is False
    assert regime_allows_directional_trade(MarketRegime.TRENDING.value) is True
