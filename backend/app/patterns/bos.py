"""
Break of Structure (BOS).

Bullish BOS:
Current High > Previous Swing High

Bearish BOS:
Current Low < Previous Swing Low
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern


class BOS(BasePattern):

    name = "Break Of Structure"

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

        df["bos"] = False
        df["bos_direction"] = ""

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

                df.at[df.index[i], "bos"] = True
                df.at[df.index[i], "bos_direction"] = "bullish"

            elif current_low < previous_low:

                df.at[df.index[i], "bos"] = True
                df.at[df.index[i], "bos_direction"] = "bearish"

        return df