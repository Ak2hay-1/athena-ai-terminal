"""Unit tests for SMC liquidity heuristics."""

from __future__ import annotations

import pandas as pd

from app.agents.smc.liquidity import analyze_liquidity


def _equal_high_series() -> pd.DataFrame:
    rows = []
    base = 1.1000
    for i in range(40):
        high = base + 0.0010
        # Create equal highs near the end
        if i in {30, 31}:
            high = 1.1050
        low = base - 0.0008
        close = base
        rows.append(
            {
                "time": pd.Timestamp("2024-01-01", tz="UTC") + pd.Timedelta(minutes=5 * i),
                "open": close,
                "high": high,
                "low": low,
                "close": close,
                "tick_volume": 150,
            }
        )
    # Sweep: wick above equal high then close back
    rows[-1]["high"] = 1.1055
    rows[-1]["close"] = 1.1040
    return pd.DataFrame(rows)


def test_equal_highs_and_pools() -> None:
    result = analyze_liquidity(_equal_high_series())
    assert result["equal_highs"] is True
    assert isinstance(result["liquidity_pools"], list)
    assert result["buy_liquidity"] or result["sell_liquidity"]


def test_sweep_or_stop_hunt_flag() -> None:
    result = analyze_liquidity(_equal_high_series())
    assert "liquidity_sweep" in result
    assert "stop_hunts" in result
    assert "inducement" in result
