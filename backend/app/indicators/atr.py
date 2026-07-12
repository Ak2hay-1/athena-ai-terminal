"""
Average True Range (ATR).
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class ATR(BaseIndicator):
    """
    Average True Range.
    """

    name = "ATR"

    def __init__(self, period: int = 14):
        self.period = period

    def calculate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        high_low = df["high"] - df["low"]

        high_close = (
            df["high"] - df["close"].shift()
        ).abs()

        low_close = (
            df["low"] - df["close"].shift()
        ).abs()

        true_range = pd.concat(
            [
                high_low,
                high_close,
                low_close,
            ],
            axis=1,
        ).max(axis=1)

        df[f"atr_{self.period}"] = (
            true_range
            .rolling(self.period)
            .mean()
        )

        return df