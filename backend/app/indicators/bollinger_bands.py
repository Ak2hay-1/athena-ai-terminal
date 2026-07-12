"""
Bollinger Bands Indicator.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class BollingerBands(BaseIndicator):
    """
    Bollinger Bands.
    """

    name = "Bollinger Bands"

    def __init__(
        self,
        period: int = 20,
        std_dev: int = 2,
    ):
        self.period = period
        self.std_dev = std_dev

    def calculate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        sma = df["close"].rolling(
            self.period
        ).mean()

        std = df["close"].rolling(
            self.period
        ).std()

        df["bb_middle"] = sma

        df["bb_upper"] = (
            sma + (std * self.std_dev)
        )

        df["bb_lower"] = (
            sma - (std * self.std_dev)
        )

        df["bb_width"] = (
            df["bb_upper"] - df["bb_lower"]
        )

        return df