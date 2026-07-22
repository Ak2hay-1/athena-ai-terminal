"""Unit tests for SMC market structure (BOS / CHOCH / HH-HL)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.agents.smc.market_structure import analyze_market_structure


def _swing_series() -> pd.DataFrame:
    """Synthetic series with clear higher highs / higher lows then break."""
    closes = [
        100, 101, 100.5, 102, 101.5, 103, 102.5, 104, 103.5, 105,
        104, 106, 105, 107, 106, 108, 107, 109, 108, 110,
        109, 108, 107, 106, 105, 104, 103, 102, 101, 100,
        99, 98, 97, 96, 95, 94, 93, 92, 91, 90,
    ]
    rows = []
    for i, c in enumerate(closes):
        rows.append(
            {
                "time": pd.Timestamp("2024-01-01", tz="UTC") + pd.Timedelta(hours=i),
                "open": c - 0.2,
                "high": c + 0.5,
                "low": c - 0.5,
                "close": c,
                "tick_volume": 100 + i,
            }
        )
    return pd.DataFrame(rows)


def test_structure_detects_trend_and_swings() -> None:
    result = analyze_market_structure(_swing_series())
    assert result["trend"] in {"BULLISH", "BEARISH", "SIDEWAYS"}
    assert isinstance(result["swing_points"], list)
    assert "bos" in result
    assert "choch" in result
    assert "hh" in result
    assert "ll" in result


def test_bos_fields_present() -> None:
    result = analyze_market_structure(_swing_series())
    bos = result["bos"]
    assert "present" in bos
    assert "direction" in bos
    assert "kind" in bos
    assert isinstance(result["internal_bos"], bool)
    assert isinstance(result["external_bos"], bool)


def test_choch_fields_present() -> None:
    result = analyze_market_structure(_swing_series())
    choch = result["choch"]
    assert "present" in choch
    assert "direction" in choch
