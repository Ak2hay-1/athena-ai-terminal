"""
Relative Strength Index (RSI).
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class RSIIndicator(BaseIndicator):
    """
    RSI (14).
    """

    def calculate(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = dataframe.copy()

        delta = df["close"].diff()

        gain = delta.clip(lower=0)

        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(
            window=14,
            min_periods=14,
        ).mean()

        avg_loss = loss.rolling(
            window=14,
            min_periods=14,
        ).mean()

        rs = avg_gain / avg_loss.replace(
            0,
            1e-10,
        )

        df["rsi_14"] = (
            100 -
            (
                100 /
                (
                    1 + rs
                )
            )
        )

        return df


rsi_indicator = RSIIndicator()