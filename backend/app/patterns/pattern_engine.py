"""
Pattern Engine.

Executes all market structure detectors.
"""

from __future__ import annotations

import pandas as pd

from app.patterns.bos import BOS
from app.patterns.choch import CHOCH
from app.patterns.fvg import FairValueGap
from app.patterns.liquidity import LiquiditySweep
from app.patterns.order_block import OrderBlock


class PatternEngine:
    """
    Main Smart Money Concepts engine.
    """

    def __init__(self):

        self.patterns = [
            BOS(),
            CHOCH(),
            FairValueGap(),
            OrderBlock(),
            LiquiditySweep(),
        ]

    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Execute all registered pattern detectors.
        """

        df = dataframe.copy()

        for pattern in self.patterns:

            df = pattern.detect(df)

        return df

    def register(self, pattern):
        """
        Register custom detector.
        """

        self.patterns.append(pattern)

    def available(self):

        return [
            pattern.name
            for pattern in self.patterns
        ]


pattern_engine = PatternEngine()