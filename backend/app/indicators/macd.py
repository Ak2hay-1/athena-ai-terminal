"""
Moving Average Convergence Divergence (MACD).
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class MACD(BaseIndicator):
    """
    MACD Indicator.
    """

    name = "MACD"

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        fast = (
            df["close"]
            .ewm(
                span=self.fast_period,
                adjust=False,
            )
            .mean()
        )

        slow = (
            df["close"]
            .ewm(
                span=self.slow_period,
                adjust=False,
            )
            .mean()
        )

        df["macd"] = fast - slow

        df["macd_signal"] = (
            df["macd"]
            .ewm(
                span=self.signal_period,
                adjust=False,
            )
            .mean()
        )

        df["macd_histogram"] = (
            df["macd"] - df["macd_signal"]
        )

        return df