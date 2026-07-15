"""
Moving Average Indicator.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class MovingAverageIndicator(BaseIndicator):
    """
    EMA Calculator.
    """

    def calculate(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = dataframe.copy()

        df["ema_9"] = (
            df["close"]
            .ewm(
                span=9,
                adjust=False,
            )
            .mean()
        )

        df["ema_20"] = (
            df["close"]
            .ewm(
                span=20,
                adjust=False,
            )
            .mean()
        )

        df["ema_50"] = (
            df["close"]
            .ewm(
                span=50,
                adjust=False,
            )
            .mean()
        )

        df["ema_100"] = (
            df["close"]
            .ewm(
                span=100,
                adjust=False,
            )
            .mean()
        )

        df["ema_200"] = (
            df["close"]
            .ewm(
                span=200,
                adjust=False,
            )
            .mean()
        )

        return df


moving_average_indicator = (
    MovingAverageIndicator()
)