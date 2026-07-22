"""
Fair value gap evidence — FVG, inverse FVG, volume imbalance.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.patterns.fair_value_gap import fair_value_gap


def analyze_fvg(dataframe: pd.DataFrame) -> dict[str, Any]:
    """
    Reuse fair_value_gap; detect inverse FVG and volume imbalance.
    """
    if dataframe.empty or len(dataframe) < 5:
        return {
            "gaps": [],
            "inverse_fvg": False,
            "volume_imbalance": False,
            "bullish_count": 0,
            "bearish_count": 0,
        }

    df = fair_value_gap.detect(dataframe)
    gaps: list[dict[str, Any]] = []
    bullish = 0
    bearish = 0
    inverse = False

    fvg_idx = df.index[df["fvg"]].tolist()
    for idx in fvg_idx[-20:]:
        row = df.loc[idx]
        direction = row.get("fvg_direction")
        upper = float(row["fvg_upper"]) if not pd.isna(row.get("fvg_upper")) else None
        lower = float(row["fvg_lower"]) if not pd.isna(row.get("fvg_lower")) else None
        size = float(row["fvg_size"]) if not pd.isna(row.get("fvg_size")) else 0.0
        gap = {
            "direction": direction,
            "upper": upper,
            "lower": lower,
            "size": size,
        }
        gaps.append(gap)
        if direction == "bullish":
            bullish += 1
        elif direction == "bearish":
            bearish += 1

        loc = df.index.get_loc(idx)
        if isinstance(loc, slice):
            continue
        after = df.iloc[int(loc) + 1 :]
        if after.empty or upper is None or lower is None:
            continue
        # Inverse FVG: gap filled then price reverses through opposite side
        filled = bool(((after["low"] <= upper) & (after["high"] >= lower)).any())
        if filled:
            if direction == "bullish" and bool((after["close"] < lower).any()):
                inverse = True
            if direction == "bearish" and bool((after["close"] > upper).any()):
                inverse = True

    # Volume imbalance: large body candle with volume >> neighbors
    volume_imbalance = False
    if "tick_volume" in df.columns and len(df) >= 5:
        last = df.iloc[-2]  # closed candle before current forming
        body = abs(float(last["close"]) - float(last["open"]))
        rng = float(last["high"]) - float(last["low"])
        vol = float(last["tick_volume"])
        avg_vol = float(df["tick_volume"].iloc[-6:-1].astype(float).mean())
        if rng > 0 and body / rng >= 0.7 and avg_vol > 0 and vol / avg_vol >= 1.8:
            volume_imbalance = True

    return {
        "gaps": gaps[-12:],
        "inverse_fvg": inverse,
        "volume_imbalance": volume_imbalance,
        "bullish_count": bullish,
        "bearish_count": bearish,
        "_dataframe": df,
    }
