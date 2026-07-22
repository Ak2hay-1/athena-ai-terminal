"""
Average Directional Index (ADX).
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class ADXIndicator(BaseIndicator):
    """
    ADX (14) with +DI / -DI.
    """

    PERIOD = 14

    def calculate(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        df = dataframe.copy()
        period = self.PERIOD

        up_move = df["high"].diff()
        down_move = -df["low"].diff()

        plus_dm = up_move.where(
            (up_move > down_move) & (up_move > 0),
            0.0,
        )
        minus_dm = down_move.where(
            (down_move > up_move) & (down_move > 0),
            0.0,
        )

        prev_close = df["close"].shift(1)
        tr = pd.concat(
            [
                df["high"] - df["low"],
                (df["high"] - prev_close).abs(),
                (df["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        atr = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        plus_di = 100 * (
            plus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
            / atr.replace(0, 1e-10)
        )
        minus_di = 100 * (
            minus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
            / atr.replace(0, 1e-10)
        )

        dx = (
            100
            * (plus_di - minus_di).abs()
            / (plus_di + minus_di).replace(0, 1e-10)
        )
        df["adx_14"] = dx.ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period,
        ).mean()
        df["plus_di_14"] = plus_di
        df["minus_di_14"] = minus_di
        return df


adx_indicator = ADXIndicator()
