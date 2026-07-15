"""
Indicator Engine.

Executes all registered indicators.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.atr import atr_indicator
from app.indicators.base_indicator import BaseIndicator
from app.indicators.bollinger import bollinger_indicator
from app.indicators.macd import macd_indicator
from app.indicators.moving_average import moving_average_indicator
from app.indicators.rsi import rsi_indicator


class IndicatorEngine:
    """
    Central indicator execution engine.
    """

    def __init__(self) -> None:

        self.indicators: list[BaseIndicator] = [

            moving_average_indicator,

            rsi_indicator,

            macd_indicator,

            atr_indicator,

            bollinger_indicator,

        ]

    # ---------------------------------------------------------

    def register(
        self,
        indicator: BaseIndicator,
    ) -> None:
        """
        Register a custom indicator.
        """

        self.indicators.append(indicator)

    # ---------------------------------------------------------

    def calculate(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Execute all indicators.
        """

        df = dataframe.copy()

        for indicator in self.indicators:

            df = indicator.calculate(df)

        return df

    # ---------------------------------------------------------

    def available(self) -> list[str]:

        return [

            indicator.__class__.__name__

            for indicator in self.indicators

        ]


indicator_engine = IndicatorEngine()