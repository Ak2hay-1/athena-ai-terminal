"""
Momentum Analyzer.

Analyzes market momentum using:
- RSI
- MACD
- MACD Histogram
"""

from __future__ import annotations

import pandas as pd


class MomentumAnalyzer:
    """
    Momentum analysis engine.
    """

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict:

        if dataframe.empty:
            return {
                "direction": "Unknown",
                "strength": 0,
            }

        row = dataframe.iloc[-1]

        rsi = float(row["rsi_14"])
        macd = float(row["macd"])
        signal = float(row["macd_signal"])
        histogram = float(row["macd_histogram"])

        score = 0

        # --------------------------
        # RSI
        # --------------------------

        if rsi >= 70:
            score -= 25

        elif rsi <= 30:
            score += 25

        elif rsi >= 55:
            score += 15

        elif rsi <= 45:
            score -= 15

        # --------------------------
        # MACD
        # --------------------------

        if macd > signal:
            score += 30

        elif macd < signal:
            score -= 30

        # --------------------------
        # Histogram
        # --------------------------

        if histogram > 0:
            score += 20

        else:
            score -= 20

        # --------------------------
        # Direction
        # --------------------------

        if score >= 40:

            direction = "Bullish"

        elif score <= -40:

            direction = "Bearish"

        else:

            direction = "Neutral"

        return {
            "direction": direction,
            "strength": abs(score),
            "score": score,
            "rsi": rsi,
            "macd": macd,
            "macd_signal": signal,
            "macd_histogram": histogram,
        }


momentum_analyzer = MomentumAnalyzer()