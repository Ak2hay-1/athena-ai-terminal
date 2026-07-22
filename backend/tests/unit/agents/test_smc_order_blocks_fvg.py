"""Unit tests for SMC order blocks and FVG."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.agents.smc.analyzer import analyze_smc
from app.agents.smc.fair_value_gap import analyze_fvg
from app.agents.smc.order_blocks import analyze_order_blocks


def _ohlcv(n: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(11)
    close = 100 + np.cumsum(rng.normal(0, 0.4, size=n))
    # Inject a clear bullish FVG mid-series
    close[40] = close[39] + 2.0
    close[41] = close[40] + 1.5
    high = close + 0.3
    low = close - 0.3
    # Create gap: previous high < next low around index 40
    high[39] = close[39] + 0.1
    low[41] = close[41] - 0.1
    low[41] = high[39] + 0.5
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC"),
            "open": close - 0.05,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": rng.integers(80, 300, size=n),
        }
    )


def test_order_blocks_structure() -> None:
    result = analyze_order_blocks(_ohlcv())
    assert "blocks" in result
    assert "breaker_blocks" in result
    assert "mitigation_blocks" in result
    assert "supply_zones" in result
    assert "demand_zones" in result
    assert isinstance(result["active_count"], int)


def test_fvg_detection_fields() -> None:
    result = analyze_fvg(_ohlcv())
    assert "gaps" in result
    assert "inverse_fvg" in result
    assert "volume_imbalance" in result
    assert isinstance(result["bullish_count"], int)
    assert isinstance(result["bearish_count"], int)


def test_analyze_smc_score_bounds() -> None:
    evidence = analyze_smc(_ohlcv(120))
    assert 0 <= evidence["score"] <= 100
    assert "bos" in evidence
    assert "fvg" in evidence
    assert "order_blocks" in evidence
