"""
Volume Weighted Average Price (VWAP).
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class VWAP(BaseIndicator):
    """
    Volume Weighted Average Price.
    """

    name = "VWAP"

    def calculate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        typical_price = (
            df["high"] +
            df["low"] +
            df["close"]
        ) / 3

        volume = df["tick_volume"]

        cumulative_tp_volume = (
            typical_price * volume
        ).cumsum()

        cumulative_volume = volume.cumsum()

        df["vwap"] = (
            cumulative_tp_volume /
            cumulative_volume
        )

        return df