"""
Volume moving average.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class VolumeMAIndicator(BaseIndicator):
    """
    Simple moving average of tick volume.
    """

    PERIOD = 20

    def calculate(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        df = dataframe.copy()
        volume = df["tick_volume"].astype(float)
        df["volume_ma_20"] = volume.rolling(
            window=self.PERIOD,
            min_periods=self.PERIOD,
        ).mean()
        df["volume_ratio"] = volume / df["volume_ma_20"].replace(0, 1e-10)
        return df


volume_ma_indicator = VolumeMAIndicator()
