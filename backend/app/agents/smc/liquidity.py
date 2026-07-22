"""
Liquidity evidence — equal highs/lows, pools, sweeps, inducement, stop hunts.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.patterns.liquidity import liquidity_sweep


def analyze_liquidity(dataframe: pd.DataFrame) -> dict[str, Any]:
    """
    Reuse liquidity_sweep and add sweep / inducement / stop-hunt heuristics.
    """
    if dataframe.empty or len(dataframe) < 10:
        return {
            "equal_highs": False,
            "equal_lows": False,
            "liquidity_pools": [],
            "liquidity_sweep": False,
            "inducement": False,
            "stop_hunts": False,
            "buy_liquidity": False,
            "sell_liquidity": False,
        }

    df = liquidity_sweep.detect(dataframe)
    recent = df.tail(40)

    equal_highs = bool(recent["equal_high"].any())
    equal_lows = bool(recent["equal_low"].any())
    buy_liq = bool(recent["buy_liquidity"].any())
    sell_liq = bool(recent["sell_liquidity"].any())

    pools: list[dict[str, Any]] = []
    for idx in recent.index[recent["equal_high"]]:
        row = recent.loc[idx]
        pools.append(
            {
                "side": "sell_side",
                "price": float(row["high"]),
                "kind": "equal_high",
            }
        )
    for idx in recent.index[recent["equal_low"]]:
        row = recent.loc[idx]
        pools.append(
            {
                "side": "buy_side",
                "price": float(row["low"]),
                "kind": "equal_low",
            }
        )

    # Liquidity sweep / stop hunt: wick beyond prior equal level, close back inside
    sweep = False
    stop_hunt = False
    inducement = False
    if len(df) >= 5:
        last = df.iloc[-1]
        window = df.iloc[-20:-1]
        eq_high_level = (
            float(window.loc[window["equal_high"], "high"].iloc[-1])
            if window["equal_high"].any()
            else None
        )
        eq_low_level = (
            float(window.loc[window["equal_low"], "low"].iloc[-1])
            if window["equal_low"].any()
            else None
        )
        if eq_high_level is not None:
            if float(last["high"]) > eq_high_level and float(last["close"]) < eq_high_level:
                sweep = True
                stop_hunt = True
        if eq_low_level is not None:
            if float(last["low"]) < eq_low_level and float(last["close"]) > eq_low_level:
                sweep = True
                stop_hunt = True

        # Inducement: small liquidity taken then reverse (sweep + opposite close bias)
        if sweep and stop_hunt:
            body = float(last["close"]) - float(last["open"])
            if abs(body) > 0:
                inducement = True

    return {
        "equal_highs": equal_highs,
        "equal_lows": equal_lows,
        "liquidity_pools": pools[-12:],
        "liquidity_sweep": sweep,
        "inducement": inducement,
        "stop_hunts": stop_hunt,
        "buy_liquidity": buy_liq,
        "sell_liquidity": sell_liq,
        "_dataframe": df,
    }
