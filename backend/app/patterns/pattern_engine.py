"""
Athena Pattern Engine.

Executes all Smart Money Concept pattern detectors.
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern
from app.patterns.break_of_structure import break_of_structure
from app.patterns.change_of_character import change_of_character
from app.patterns.fair_value_gap import fair_value_gap
from app.patterns.liquidity import liquidity_sweep
from app.patterns.order_block import order_block
from app.patterns.premium_discount import premium_discount
from app.patterns.swing_detector import swing_detector
from app.patterns.trend_structure import trend_structure


class PatternEngine:
    """
    Executes all registered pattern detectors.
    """

    def __init__(self) -> None:

        self.patterns: list[BasePattern] = [

            swing_detector,

            trend_structure,

            break_of_structure,

            change_of_character,

            fair_value_gap,

            order_block,

            liquidity_sweep,

            premium_discount,

        ]

    def register(
        self,
        pattern: BasePattern,
    ) -> None:

        self.patterns.append(pattern)

    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = dataframe.copy()

        for pattern in self.patterns:

            df = pattern.detect(df)

        return df

    def available(self) -> list[str]:

        return [

            pattern.__class__.__name__

            for pattern in self.patterns

        ]


pattern_engine = PatternEngine()
