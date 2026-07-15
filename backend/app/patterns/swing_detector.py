"""
Swing High / Swing Low Detector.
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern


class SwingDetector(BasePattern):
    """
    Detect swing highs and swing lows.

    A swing high is a candle whose high is greater than
    N candles before and after.

    A swing low is a candle whose low is lower than
    N candles before and after.
    """

    def __init__(
        self,
        lookback: int = 3,
    ) -> None:

        self.lookback = lookback

    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = dataframe.copy()

        df["swing_high"] = False
        df["swing_low"] = False

        length = len(df)

        for i in range(
            self.lookback,
            length - self.lookback,
        ):

            high = df.iloc[i]["high"]

            left_high = df.iloc[
                i - self.lookback:i
            ]["high"].max()

            right_high = df.iloc[
                i + 1:i + self.lookback + 1
            ]["high"].max()

            if high > left_high and high > right_high:

                df.at[df.index[i], "swing_high"] = True

            low = df.iloc[i]["low"]

            left_low = df.iloc[
                i - self.lookback:i
            ]["low"].min()

            right_low = df.iloc[
                i + 1:i + self.lookback + 1
            ]["low"].min()

            if low < left_low and low < right_low:

                df.at[df.index[i], "swing_low"] = True

        return df


swing_detector = SwingDetector()