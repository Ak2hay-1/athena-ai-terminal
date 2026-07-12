"""
Base class for all indicators.
"""

from __future__ import annotations

import pandas as pd


class BaseIndicator:

    name = "Base"

    def calculate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        raise NotImplementedError
    