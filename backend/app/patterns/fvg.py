"""
Fair Value Gap (FVG)

Bullish FVG:
Candle1.high < Candle3.low

Bearish FVG:
Candle1.low > Candle3.high
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern


class FairValueGap(BasePattern):
    """
    Detect Fair Value Gaps.
    """

    name = "Fair Value Gap"

    def detect(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        df["fvg"] = False
        df["fvg_direction"] = ""
        df["fvg_top"] = None
        df["fvg_bottom"] = None

        for i in range(2, len(df)):

            candle1 = df.iloc[i - 2]
            candle3 = df.iloc[i]

            # Bullish FVG
            if candle1["high"] < candle3["low"]:

                df.at[df.index[i], "fvg"] = True
                df.at[df.index[i], "fvg_direction"] = "bullish"
                df.at[df.index[i], "fvg_top"] = candle3["low"]
                df.at[df.index[i], "fvg_bottom"] = candle1["high"]

            # Bearish FVG
            elif candle1["low"] > candle3["high"]:

                df.at[df.index[i], "fvg"] = True
                df.at[df.index[i], "fvg_direction"] = "bearish"
                df.at[df.index[i], "fvg_top"] = candle1["low"]
                df.at[df.index[i], "fvg_bottom"] = candle3["high"]

        return df