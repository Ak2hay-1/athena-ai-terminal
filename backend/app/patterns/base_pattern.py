"""
Base Pattern Class.
"""

from __future__ import annotations

import pandas as pd


class BasePattern:
    """
    Base class for all market structure patterns.
    """

    name = "Base Pattern"

    def detect(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        raise NotImplementedError