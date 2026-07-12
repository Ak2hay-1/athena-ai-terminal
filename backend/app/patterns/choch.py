"""
Change of Character (CHOCH).

Detects a change in market direction after a confirmed BOS.
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern


class CHOCH(BasePattern):
    """
    Change of Character.
    """

    name = "CHOCH"

    def __init__(
        self,
        lookback: int = 5,
    ):
        self.lookback = lookback

    def detect(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        df["choch"] = False
        df["choch_direction"] = ""

        last_structure = None

        for i in range(self.lookback, len(df)):

            previous_high = (
                df["high"]
                .iloc[i - self.lookback:i]
                .max()
            )

            previous_low = (
                df["low"]
                .iloc[i - self.lookback:i]
                .min()
            )

            current_high = df.iloc[i]["high"]
            current_low = df.iloc[i]["low"]

            if current_high > previous_high:

                if last_structure == "bearish":
                    df.at[df.index[i], "choch"] = True
                    df.at[df.index[i], "choch_direction"] = "bullish"

                last_structure = "bullish"

            elif current_low < previous_low:

                if last_structure == "bullish":
                    df.at[df.index[i], "choch"] = True
                    df.at[df.index[i], "choch_direction"] = "bearish"

                last_structure = "bearish"

        return df