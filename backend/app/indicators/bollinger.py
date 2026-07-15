"""
Bollinger Bands.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class BollingerBandsIndicator(BaseIndicator):
    """
    Bollinger Bands (20,2)
    """

    PERIOD = 20

    STD = 2

    def calculate(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = dataframe.copy()

        middle = (
            df["close"]
            .rolling(
                self.PERIOD,
                min_periods=self.PERIOD,
            )
            .mean()
        )

        std = (
            df["close"]
            .rolling(
                self.PERIOD,
                min_periods=self.PERIOD,
            )
            .std()
        )

        df["bb_middle"] = middle

        df["bb_upper"] = (
            middle +
            (std * self.STD)
        )

        df["bb_lower"] = (
            middle -
            (std * self.STD)
        )

        df["bb_width"] = (
            (
                df["bb_upper"] -
                df["bb_lower"]
            )
            / middle.replace(
                0,
                1e-10,
            )
        ) * 100

        df["bb_squeeze"] = (
            df["bb_width"] < 5
        )

        return df


bollinger_indicator = (
    BollingerBandsIndicator()
)