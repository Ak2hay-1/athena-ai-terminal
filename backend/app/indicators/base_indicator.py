"""
Base Indicator.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

import pandas as pd


class BaseIndicator(ABC):
    """
    Base class for all indicators.
    """

    @abstractmethod
    def calculate(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculate indicator.
        """
        raise NotImplementedError