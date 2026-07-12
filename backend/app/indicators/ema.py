"""
EMA Indicator.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class EMA(BaseIndicator):

    name = "EMA"

    def __init__(
        self,
        period: int = 20,
    ):

        self.period = period

    def calculate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        df[f"ema_{self.period}"] = (
            df["close"]
            .ewm(
                span=self.period,
                adjust=False,
            )
            .mean()
        )

        return df