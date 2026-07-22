"""
Market structure evidence — BOS, CHOCH, HH/HL/LH/LL, swing points.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.patterns.break_of_structure import break_of_structure
from app.patterns.change_of_character import change_of_character
from app.patterns.swing_detector import swing_detector
from app.patterns.trend_structure import trend_structure


def _iso(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def analyze_market_structure(dataframe: pd.DataFrame) -> dict[str, Any]:
    """
    Build structure evidence from existing pattern detectors.
    Classifies internal vs external BOS relative to prior swing extremes.
    """
    if dataframe.empty or len(dataframe) < 20:
        return {
            "trend": "SIDEWAYS",
            "hh": False,
            "hl": False,
            "lh": False,
            "ll": False,
            "swing_points": [],
            "bos": {"present": False, "direction": None, "kind": None, "level": None},
            "choch": {"present": False, "direction": None},
            "internal_bos": False,
            "external_bos": False,
        }

    df = swing_detector.detect(dataframe)
    df = trend_structure.detect(df)
    df = break_of_structure.detect(df)
    df = change_of_character.detect(df)

    last = df.iloc[-1]
    swing_highs = df.loc[df["swing_high"], ["time", "high"]].tail(8)
    swing_lows = df.loc[df["swing_low"], ["time", "low"]].tail(8)

    swing_points: list[dict[str, Any]] = []
    for _, row in swing_highs.iterrows():
        swing_points.append(
            {
                "type": "swing_high",
                "price": float(row["high"]),
                "time": _iso(row.get("time")),
            }
        )
    for _, row in swing_lows.iterrows():
        swing_points.append(
            {
                "type": "swing_low",
                "price": float(row["low"]),
                "time": _iso(row.get("time")),
            }
        )

    # Recent BOS on last confirmed bars
    bos_rows = df[df["bos"]].tail(3)
    bos_present = bool(last.get("bos")) or len(bos_rows) > 0
    bos_direction = None
    bos_level = None
    if len(bos_rows):
        bos_direction = bos_rows.iloc[-1].get("bos_direction")
        level = bos_rows.iloc[-1].get("broken_level")
        bos_level = float(level) if level is not None and not pd.isna(level) else None
    elif bos_present:
        bos_direction = last.get("bos_direction")
        level = last.get("broken_level")
        bos_level = float(level) if level is not None and not pd.isna(level) else None

    # Internal vs external: external if break beyond max/min of last N swings
    range_high = float(df["high"].tail(50).max())
    range_low = float(df["low"].tail(50).min())
    price = float(last["close"])
    external_bos = False
    internal_bos = False
    if bos_present and bos_direction == "bullish":
        external_bos = price >= range_high * 0.999 or (
            bos_level is not None and bos_level >= range_high * 0.998
        )
        internal_bos = not external_bos
    elif bos_present and bos_direction == "bearish":
        external_bos = price <= range_low * 1.001 or (
            bos_level is not None and bos_level <= range_low * 1.002
        )
        internal_bos = not external_bos

    choch_rows = df[df["choch"]].tail(3)
    choch_present = bool(last.get("choch")) or len(choch_rows) > 0
    choch_direction = None
    if len(choch_rows):
        choch_direction = choch_rows.iloc[-1].get("choch_direction")
    elif choch_present:
        choch_direction = last.get("choch_direction")

    # Recent structure labels
    recent = df.tail(30)
    return {
        "trend": str(last.get("trend") or "SIDEWAYS"),
        "hh": bool(recent["hh"].any()),
        "hl": bool(recent["hl"].any()),
        "lh": bool(recent["lh"].any()),
        "ll": bool(recent["ll"].any()),
        "swing_points": swing_points,
        "bos": {
            "present": bos_present,
            "direction": bos_direction,
            "kind": (
                "external"
                if external_bos
                else ("internal" if internal_bos else None)
            ),
            "level": bos_level,
        },
        "choch": {
            "present": choch_present,
            "direction": choch_direction,
        },
        "internal_bos": internal_bos,
        "external_bos": external_bos,
        "_dataframe": df,
    }
