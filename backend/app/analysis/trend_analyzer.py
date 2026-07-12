"""
Trend Analyzer.

Determines market trend using EMAs.
"""

from __future__ import annotations

import pandas as pd


class TrendAnalyzer:
    """
    Analyze overall market trend.
    """

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict:

        if dataframe.empty:
            return {
                "trend": "Unknown",
                "strength": 0,
            }

        row = dataframe.iloc[-1]

        ema20 = row["ema_20"]
        ema50 = row["ema_50"]
        ema200 = row["ema_200"]

        trend = "Sideways"
        strength = 50

        if ema20 > ema50 > ema200:

            trend = "Bullish"

            strength = 100

        elif ema20 < ema50 < ema200:

            trend = "Bearish"

            strength = 100

        elif ema20 > ema50:

            trend = "Weak Bullish"

            strength = 70

        elif ema20 < ema50:

            trend = "Weak Bearish"

            strength = 70

        return {
            "trend": trend,
            "strength": strength,
            "ema20": float(ema20),
            "ema50": float(ema50),
            "ema200": float(ema200),
        }


trend_analyzer = TrendAnalyzer()