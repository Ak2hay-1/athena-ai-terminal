"""
Average True Range (ATR).
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class ATRIndicator(BaseIndicator):
    """
    Average True Range (ATR 14)
    """

    PERIOD = 14

    def calculate(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = dataframe.copy()

        previous_close = df["close"].shift(1)

        tr1 = df["high"] - df["low"]

        tr2 = (
            df["high"] - previous_close
        ).abs()

        tr3 = (
            df["low"] - previous_close
        ).abs()

        df["true_range"] = pd.concat(
            [tr1, tr2, tr3],
            axis=1,
        ).max(axis=1)

        df["atr_14"] = (
            df["true_range"]
            .rolling(
                self.PERIOD,
                min_periods=self.PERIOD,
            )
            .mean()
        )

        return df


atr_indicator = ATRIndicator()