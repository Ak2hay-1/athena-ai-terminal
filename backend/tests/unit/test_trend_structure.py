"""Tests for trend structure detection."""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock

import pandas as pd

from app.patterns.trend_structure import TrendStructure

trend_structure_module = importlib.import_module(
    "app.patterns.trend_structure"
)


def _ohlc(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [1.0] * n,
            "high": [1.0] * n,
            "low": [1.0] * n,
            "close": [1.0] * n,
        }
    )


def _patch_swings(monkeypatch, fake_swing) -> None:
    monkeypatch.setattr(
        trend_structure_module,
        "swing_detector",
        MagicMock(detect=fake_swing),
    )


def test_bullish_when_hh_and_hl_on_different_bars(monkeypatch):
    df = _ohlc(10)
    df.loc[1, "high"] = 10.0
    df.loc[5, "high"] = 12.0
    df.loc[3, "low"] = 5.0
    df.loc[7, "low"] = 6.0

    def fake_swing(dataframe: pd.DataFrame) -> pd.DataFrame:
        out = dataframe.copy()
        out["swing_high"] = False
        out["swing_low"] = False
        out.loc[1, "swing_high"] = True
        out.loc[5, "swing_high"] = True
        out.loc[3, "swing_low"] = True
        out.loc[7, "swing_low"] = True
        return out

    _patch_swings(monkeypatch, fake_swing)

    result = TrendStructure().detect(df)

    assert bool(result.loc[5, "hh"]) is True
    assert bool(result.loc[7, "hl"]) is True
    assert result.loc[7, "trend"] == "BULLISH"
    assert result.loc[9, "trend"] == "BULLISH"


def test_bearish_when_lh_and_ll_on_different_bars(monkeypatch):
    df = _ohlc(10)
    df.loc[1, "high"] = 12.0
    df.loc[5, "high"] = 10.0
    df.loc[3, "low"] = 6.0
    df.loc[7, "low"] = 5.0

    def fake_swing(dataframe: pd.DataFrame) -> pd.DataFrame:
        out = dataframe.copy()
        out["swing_high"] = False
        out["swing_low"] = False
        out.loc[1, "swing_high"] = True
        out.loc[5, "swing_high"] = True
        out.loc[3, "swing_low"] = True
        out.loc[7, "swing_low"] = True
        return out

    _patch_swings(monkeypatch, fake_swing)

    result = TrendStructure().detect(df)

    assert bool(result.loc[5, "lh"]) is True
    assert bool(result.loc[7, "ll"]) is True
    assert result.loc[7, "trend"] == "BEARISH"
    assert result.loc[9, "trend"] == "BEARISH"


def test_sideways_until_both_swing_structures_exist(monkeypatch):
    df = _ohlc(6)
    df.loc[1, "high"] = 10.0
    df.loc[4, "high"] = 12.0

    def fake_swing(dataframe: pd.DataFrame) -> pd.DataFrame:
        out = dataframe.copy()
        out["swing_high"] = False
        out["swing_low"] = False
        out.loc[1, "swing_high"] = True
        out.loc[4, "swing_high"] = True
        return out

    _patch_swings(monkeypatch, fake_swing)

    result = TrendStructure().detect(df)

    assert bool(result.loc[4, "hh"]) is True
    assert result.loc[5, "trend"] == "SIDEWAYS"
