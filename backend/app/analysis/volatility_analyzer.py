"""
Volatility Analyzer.

Analyzes market volatility using:
- ATR
- Bollinger Band Width
- Candle Range
"""

from __future__ import annotations

import pandas as pd


class VolatilityAnalyzer:
    """
    Volatility analysis engine.
    """

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict:

        if dataframe.empty:
            return {
                "level": "Unknown",
                "score": 0,
            }

        row = dataframe.iloc[-1]

        atr = float(row["atr_14"])
        bb_width = float(row["bb_width"])

        candle_range = float(
            row["high"] - row["low"]
        )

        score = 0

        # ATR

        if atr > 20:
            score += 40
        elif atr > 10:
            score += 30
        elif atr > 5:
            score += 20
        else:
            score += 10

        # Bollinger Width

        if bb_width > 30:
            score += 40
        elif bb_width > 15:
            score += 30
        elif bb_width > 8:
            score += 20
        else:
            score += 10

        # Candle Range

        if candle_range > atr:
            score += 20

        score = min(score, 100)

        if score >= 85:
            level = "Extreme"

        elif score >= 70:
            level = "High"

        elif score >= 50:
            level = "Medium"

        elif score >= 25:
            level = "Low"

        else:
            level = "Very Low"

        return {
            "level": level,
            "score": score,
            "atr": atr,
            "bb_width": bb_width,
            "candle_range": candle_range,
        }


volatility_analyzer = VolatilityAnalyzer()