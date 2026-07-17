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

    Trend is derived from the most recent swing-high and swing-low
    classifications across bars (not required on the same candle):

    - HH + HL → BULLISH
    - LH + LL → BEARISH
    - otherwise keep the prior trend (default SIDEWAYS)
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
        last_high_structure: str | None = None
        last_low_structure: str | None = None
        current_trend = "SIDEWAYS"

        for i in range(len(df)):

            row = df.iloc[i]
            idx = df.index[i]

            # -------------------------
            # Swing High
            # -------------------------

            if row["swing_high"]:

                if previous_high is not None:

                    if row["high"] > previous_high:

                        df.at[idx, "hh"] = True
                        last_high_structure = "HH"

                    else:

                        df.at[idx, "lh"] = True
                        last_high_structure = "LH"

                previous_high = row["high"]

            # -------------------------
            # Swing Low
            # -------------------------

            if row["swing_low"]:

                if previous_low is not None:

                    if row["low"] > previous_low:

                        df.at[idx, "hl"] = True
                        last_low_structure = "HL"

                    else:

                        df.at[idx, "ll"] = True
                        last_low_structure = "LL"

                previous_low = row["low"]

            # -------------------------
            # Trend (across swing sequence)
            # -------------------------

            if last_high_structure == "HH" and last_low_structure == "HL":
                current_trend = "BULLISH"
            elif last_high_structure == "LH" and last_low_structure == "LL":
                current_trend = "BEARISH"

            df.at[idx, "trend"] = current_trend

        return df


trend_structure = TrendStructure()
