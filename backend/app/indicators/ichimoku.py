"""
Ichimoku Cloud.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class IchimokuIndicator(BaseIndicator):
    """
    Standard Ichimoku (9, 26, 52).
    """

    TENKAN = 9
    KIJUN = 26
    SENKOU_B = 52
    DISPLACEMENT = 26

    def calculate(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        df = dataframe.copy()

        def mid(high_low_window: int) -> pd.Series:
            high = df["high"].rolling(window=high_low_window, min_periods=high_low_window).max()
            low = df["low"].rolling(window=high_low_window, min_periods=high_low_window).min()
            return (high + low) / 2

        tenkan = mid(self.TENKAN)
        kijun = mid(self.KIJUN)
        senkou_a = ((tenkan + kijun) / 2).shift(self.DISPLACEMENT)
        senkou_b = mid(self.SENKOU_B).shift(self.DISPLACEMENT)
        chikou = df["close"].shift(-self.DISPLACEMENT)

        df["ichimoku_tenkan"] = tenkan
        df["ichimoku_kijun"] = kijun
        df["ichimoku_senkou_a"] = senkou_a
        df["ichimoku_senkou_b"] = senkou_b
        df["ichimoku_chikou"] = chikou
        return df


ichimoku_indicator = IchimokuIndicator()
