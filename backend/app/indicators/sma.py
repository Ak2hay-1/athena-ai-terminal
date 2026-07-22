"""
Simple Moving Average (SMA).
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class SMAIndicator(BaseIndicator):
    """
    SMA for common lookbacks on close.
    """

    PERIODS = (9, 20, 50, 200)

    def calculate(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        df = dataframe.copy()
        for period in self.PERIODS:
            df[f"sma_{period}"] = (
                df["close"]
                .rolling(window=period, min_periods=period)
                .mean()
            )
        return df


sma_indicator = SMAIndicator()
