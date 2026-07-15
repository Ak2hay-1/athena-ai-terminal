"""
Break Of Structure (BOS).
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern
from app.patterns.swing_detector import (
    swing_detector,
)


class BreakOfStructure(BasePattern):
    """
    Detect Bullish/Bearish BOS.
    """

    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = swing_detector.detect(dataframe)

        df["bos"] = False
        df["bos_direction"] = None
        df["broken_level"] = None

        last_swing_high = None
        last_swing_low = None

        for i in range(len(df)):

            row = df.iloc[i]

            if row["swing_high"]:

                last_swing_high = row["high"]

            if row["swing_low"]:

                last_swing_low = row["low"]

            if (
                last_swing_high is not None
                and row["close"] > last_swing_high
            ):

                df.at[df.index[i], "bos"] = True

                df.at[
                    df.index[i],
                    "bos_direction",
                ] = "bullish"

                df.at[
                    df.index[i],
                    "broken_level",
                ] = last_swing_high

            elif (
                last_swing_low is not None
                and row["close"] < last_swing_low
            ):

                df.at[df.index[i], "bos"] = True

                df.at[
                    df.index[i],
                    "bos_direction",
                ] = "bearish"

                df.at[
                    df.index[i],
                    "broken_level",
                ] = last_swing_low

        return df


break_of_structure = BreakOfStructure()