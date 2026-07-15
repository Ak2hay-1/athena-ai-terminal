"""
Fair Value Gap (FVG).

Three-candle imbalance detection.
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern


class FairValueGap(BasePattern):
    """
    Detect Bullish/Bearish Fair Value Gaps.
    """

    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = dataframe.copy()

        df["fvg"] = False
        df["fvg_direction"] = None
        df["fvg_upper"] = None
        df["fvg_lower"] = None
        df["fvg_size"] = 0.0

        for i in range(1, len(df) - 1):

            previous = df.iloc[i - 1]

            current = df.iloc[i]

            nxt = df.iloc[i + 1]

            # -------------------------
            # Bullish FVG
            # -------------------------

            if previous["high"] < nxt["low"]:

                df.at[df.index[i], "fvg"] = True

                df.at[
                    df.index[i],
                    "fvg_direction",
                ] = "bullish"

                df.at[
                    df.index[i],
                    "fvg_upper",
                ] = nxt["low"]

                df.at[
                    df.index[i],
                    "fvg_lower",
                ] = previous["high"]

                df.at[
                    df.index[i],
                    "fvg_size",
                ] = (
                    nxt["low"]
                    - previous["high"]
                )

            # -------------------------
            # Bearish FVG
            # -------------------------

            elif previous["low"] > nxt["high"]:

                df.at[df.index[i], "fvg"] = True

                df.at[
                    df.index[i],
                    "fvg_direction",
                ] = "bearish"

                df.at[
                    df.index[i],
                    "fvg_upper",
                ] = previous["low"]

                df.at[
                    df.index[i],
                    "fvg_lower",
                ] = nxt["high"]

                df.at[
                    df.index[i],
                    "fvg_size",
                ] = (
                    previous["low"]
                    - nxt["high"]
                )

        return df


fair_value_gap = FairValueGap()