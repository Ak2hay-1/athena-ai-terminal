"""
Indicator Engine.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.atr import ATR
from app.indicators.ema import EMA
from app.indicators.macd import MACD
from app.indicators.rsi import RSI


class IndicatorEngine:
    """
    Central indicator calculation engine.
    """

    def __init__(self):

        self.indicators = [
            EMA(20),
            EMA(50),
            EMA(200),
            RSI(14),
            MACD(),
            ATR(),
        ]

    def calculate(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = dataframe.copy()

        for indicator in self.indicators:
            df = indicator.calculate(df)

        return df

    def register(self, indicator):

        self.indicators.append(indicator)

    def available(self):

        return [
            indicator.name
            for indicator in self.indicators
        ]


indicator_engine = IndicatorEngine()