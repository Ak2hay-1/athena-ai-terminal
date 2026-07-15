"""
MACD Indicator.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class MACDIndicator(BaseIndicator):
    """
    MACD 12/26/9
    """

    def calculate(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = dataframe.copy()

        ema12 = (
            df["close"]
            .ewm(
                span=12,
                adjust=False,
            )
            .mean()
        )

        ema26 = (
            df["close"]
            .ewm(
                span=26,
                adjust=False,
            )
            .mean()
        )

        df["macd"] = ema12 - ema26

        df["macd_signal"] = (
            df["macd"]
            .ewm(
                span=9,
                adjust=False,
            )
            .mean()
        )

        df["macd_histogram"] = (
            df["macd"] -
            df["macd_signal"]
        )

        df["macd_bullish"] = (
            df["macd"] >
            df["macd_signal"]
        )

        df["macd_bearish"] = (
            df["macd"] <
            df["macd_signal"]
        )

        return df


macd_indicator = MACDIndicator()
