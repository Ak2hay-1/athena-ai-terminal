"""
Premium / Discount Zones.
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern


class PremiumDiscount(BasePattern):
    """
    Calculate premium and discount zones.

    Uses rolling swing range.
    """

    WINDOW = 50

    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = dataframe.copy()

        df["range_high"] = (
            df["high"]
            .rolling(self.WINDOW)
            .max()
        )

        df["range_low"] = (
            df["low"]
            .rolling(self.WINDOW)
            .min()
        )

        df["equilibrium"] = (
            df["range_high"] +
            df["range_low"]
        ) / 2

        df["premium"] = (
            df["close"] >
            df["equilibrium"]
        )

        df["discount"] = (
            df["close"] <
            df["equilibrium"]
        )

        df["premium_percent"] = (
            (
                df["close"] -
                df["range_low"]
            )
            /
            (
                df["range_high"] -
                df["range_low"]
            ).replace(0, 1e-10)
        ) * 100

        return df


premium_discount = PremiumDiscount()