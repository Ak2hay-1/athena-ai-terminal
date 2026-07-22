"""
Stochastic RSI.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.base_indicator import BaseIndicator


class StochasticRSIIndicator(BaseIndicator):
    """
    Stochastic RSI (14, 14, 3, 3).
    """

    RSI_PERIOD = 14
    STOCH_PERIOD = 14
    K_SMOOTH = 3
    D_SMOOTH = 3

    def calculate(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        df = dataframe.copy()

        if "rsi_14" not in df.columns:
            delta = df["close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(
                window=self.RSI_PERIOD,
                min_periods=self.RSI_PERIOD,
            ).mean()
            avg_loss = loss.rolling(
                window=self.RSI_PERIOD,
                min_periods=self.RSI_PERIOD,
            ).mean()
            rs = avg_gain / avg_loss.replace(0, 1e-10)
            rsi = 100 - (100 / (1 + rs))
        else:
            rsi = df["rsi_14"]

        lowest = rsi.rolling(
            window=self.STOCH_PERIOD,
            min_periods=self.STOCH_PERIOD,
        ).min()
        highest = rsi.rolling(
            window=self.STOCH_PERIOD,
            min_periods=self.STOCH_PERIOD,
        ).max()
        stoch = (rsi - lowest) / (highest - lowest).replace(0, 1e-10)

        df["stoch_rsi_k"] = (
            stoch.rolling(window=self.K_SMOOTH, min_periods=self.K_SMOOTH).mean()
            * 100
        )
        df["stoch_rsi_d"] = (
            df["stoch_rsi_k"]
            .rolling(window=self.D_SMOOTH, min_periods=self.D_SMOOTH)
            .mean()
        )
        return df


stochastic_rsi_indicator = StochasticRSIIndicator()
