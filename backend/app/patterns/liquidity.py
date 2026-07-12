"""
Liquidity Detection Engine.

Detects:

- Buy Side Liquidity
- Sell Side Liquidity
- Liquidity Sweeps
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern


class LiquiditySweep(BasePattern):
    """
    Detect liquidity pools and sweeps.
    """

    name = "Liquidity Sweep"

    def __init__(
        self,
        tolerance: float = 0.10,
    ):
        self.tolerance = tolerance

    def detect(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        df["buy_side_liquidity"] = False
        df["sell_side_liquidity"] = False

        df["buy_side_sweep"] = False
        df["sell_side_sweep"] = False

        for i in range(2, len(df)):

            previous = df.iloc[i - 1]
            current = df.iloc[i]

            # --------------------------
            # Buy Side Liquidity
            # --------------------------

            if abs(
                previous["high"] - current["high"]
            ) <= self.tolerance:

                df.at[df.index[i], "buy_side_liquidity"] = True

            # --------------------------
            # Sell Side Liquidity
            # --------------------------

            if abs(
                previous["low"] - current["low"]
            ) <= self.tolerance:

                df.at[df.index[i], "sell_side_liquidity"] = True

            # --------------------------
            # Buy Side Sweep
            # --------------------------

            if (
                current["high"] > previous["high"]
                and current["close"] < previous["high"]
            ):

                df.at[df.index[i], "buy_side_sweep"] = True

            # --------------------------
            # Sell Side Sweep
            # --------------------------

            if (
                current["low"] < previous["low"]
                and current["close"] > previous["low"]
            ):

                df.at[df.index[i], "sell_side_sweep"] = True

        return df