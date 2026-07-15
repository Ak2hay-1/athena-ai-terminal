"""
Base Pattern.

Every Smart Money Concept pattern inherits from this class.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

import pandas as pd


class BasePattern(ABC):
    """
    Abstract base class for all market patterns.
    """

    @abstractmethod
    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Detect pattern.

        Returns:
            Updated DataFrame.
        """
        raise NotImplementedError