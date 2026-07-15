"""
Change Of Character (CHOCH).
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern
from app.patterns.break_of_structure import break_of_structure


class ChangeOfCharacter(BasePattern):
    """
    Detect Change Of Character.

    CHOCH occurs when market structure shifts from
    bullish to bearish or bearish to bullish.
    """

    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = break_of_structure.detect(dataframe)

        df["choch"] = False
        df["choch_direction"] = None

        previous_direction = None

        for i in range(len(df)):

            direction = df.iloc[i]["bos_direction"]

            if direction is None:
                continue

            if previous_direction is None:

                previous_direction = direction

                continue

            if direction != previous_direction:

                df.at[df.index[i], "choch"] = True

                df.at[
                    df.index[i],
                    "choch_direction",
                ] = direction

            previous_direction = direction

        return df


change_of_character = ChangeOfCharacter()