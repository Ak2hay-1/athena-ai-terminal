"""
Order block evidence — OB, breaker, mitigation, supply/demand.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.patterns.order_block import order_block


def analyze_order_blocks(dataframe: pd.DataFrame) -> dict[str, Any]:
    """
    Reuse order_block detector; classify breaker/mitigation/supply/demand.
    """
    if dataframe.empty or len(dataframe) < 20:
        return {
            "blocks": [],
            "breaker_blocks": [],
            "mitigation_blocks": [],
            "supply_zones": [],
            "demand_zones": [],
            "active_count": 0,
        }

    df = order_block.detect(dataframe)
    blocks: list[dict[str, Any]] = []
    breakers: list[dict[str, Any]] = []
    mitigations: list[dict[str, Any]] = []
    supply: list[dict[str, Any]] = []
    demand: list[dict[str, Any]] = []

    ob_indices = df.index[df["order_block"]].tolist()
    for idx in ob_indices[-15:]:
        row = df.loc[idx]
        direction = row.get("ob_direction")
        high = float(row["ob_high"]) if not pd.isna(row.get("ob_high")) else float(row["high"])
        low = float(row["ob_low"]) if not pd.isna(row.get("ob_low")) else float(row["low"])
        block = {
            "direction": direction,
            "high": high,
            "low": low,
            "index": int(df.index.get_loc(idx)) if not isinstance(idx, int) else int(idx),
        }
        blocks.append(block)

        if direction == "bearish":
            supply.append({"high": high, "low": low})
        elif direction == "bullish":
            demand.append({"high": high, "low": low})

        # Mitigation: later price traded through the block
        loc = df.index.get_loc(idx)
        if isinstance(loc, slice):
            continue
        after = df.iloc[int(loc) + 1 :]
        if after.empty:
            continue
        mitigated = False
        broken = False
        if direction == "bullish":
            mitigated = bool((after["low"] <= high).any() and (after["low"] >= low).any())
            broken = bool((after["close"] < low).any())
        elif direction == "bearish":
            mitigated = bool((after["high"] >= low).any() and (after["high"] <= high).any())
            broken = bool((after["close"] > high).any())

        if mitigated:
            mitigations.append(block)
        if broken:
            # Breaker: OB invalidated then acts opposite
            breaker = {**block, "kind": "breaker"}
            breakers.append(breaker)

    return {
        "blocks": blocks,
        "breaker_blocks": breakers,
        "mitigation_blocks": mitigations,
        "supply_zones": supply[-8:],
        "demand_zones": demand[-8:],
        "active_count": len(blocks),
        "_dataframe": df,
    }
