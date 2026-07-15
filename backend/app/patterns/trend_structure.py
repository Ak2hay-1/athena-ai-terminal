"""
Trend Structure Detection.

Detects:

- Higher High (HH)
- Higher Low (HL)
- Lower High (LH)
- Lower Low (LL)
- Trend
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern
from app.patterns.swing_detector import swing_detector


class TrendStructure(BasePattern):
    """
    Detect market structure.
    """

    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = swing_detector.detect(dataframe)

        df["hh"] = False
        df["hl"] = False
        df["lh"] = False
        df["ll"] = False

        df["trend"] = "SIDEWAYS"

        previous_high = None
        previous_low = None

        for i in range(len(df)):

            row = df.iloc[i]

            # -------------------------
            # Swing High
            # -------------------------

            if row["swing_high"]:

                if previous_high is not None:

                    if row["high"] > previous_high:

                        df.at[df.index[i], "hh"] = True

                    else:

                        df.at[df.index[i], "lh"] = True

                previous_high = row["high"]

            # -------------------------
            # Swing Low
            # -------------------------

            if row["swing_low"]:

                if previous_low is not None:

                    if row["low"] > previous_low:

                        df.at[df.index[i], "hl"] = True

                    else:

                        df.at[df.index[i], "ll"] = True

                previous_low = row["low"]

            # -------------------------
            # Trend
            # -------------------------

            if (
                df.at[df.index[i], "hh"]
                and df.at[df.index[i], "hl"]
            ):

                df.at[df.index[i], "trend"] = "BULLISH"

            elif (
                df.at[df.index[i], "lh"]
                and df.at[df.index[i], "ll"]
            ):

                df.at[df.index[i], "trend"] = "BEARISH"

        return df


trend_structure = TrendStructure()
