"""
Liquidity Detection.
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern


class LiquiditySweep(BasePattern):
    """
    Detect Equal Highs and Equal Lows.
    """

    def __init__(
        self,
        tolerance: float = 0.0005,
    ) -> None:

        self.tolerance = tolerance

    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = dataframe.copy()

        df["equal_high"] = False
        df["equal_low"] = False

        df["buy_liquidity"] = False
        df["sell_liquidity"] = False

        for i in range(1, len(df)):

            previous = df.iloc[i - 1]

            current = df.iloc[i]

            # Equal High

            if abs(
                current["high"] -
                previous["high"]
            ) <= self.tolerance:

                df.at[
                    df.index[i],
                    "equal_high",
                ] = True

                df.at[
                    df.index[i],
                    "buy_liquidity",
                ] = True

            # Equal Low

            if abs(
                current["low"] -
                previous["low"]
            ) <= self.tolerance:

                df.at[
                    df.index[i],
                    "equal_low",
                ] = True

                df.at[
                    df.index[i],
                    "sell_liquidity",
                ] = True

        return df


liquidity_sweep = LiquiditySweep()
