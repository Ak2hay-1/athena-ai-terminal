"""
Athena Multi Timeframe Analyzer.
"""

from __future__ import annotations

import pandas as pd

from app.analysis.market_analyzer import market_analyzer


class MultiTimeframeAnalyzer:
    """
    Analyze multiple timeframes and build a combined summary.

    Expected input:

    {
        "M1": dataframe,
        "M5": dataframe,
        "M15": dataframe,
        "H1": dataframe,
        "H4": dataframe,
    }
    """

    def analyze(
        self,
        frames: dict[str, pd.DataFrame],
    ) -> dict:

        results: dict[str, dict] = {}

        bullish = 0
        bearish = 0

        for timeframe, dataframe in frames.items():

            if dataframe.empty:
                continue

            analysis = market_analyzer.analyze(
                dataframe
            )

            results[timeframe] = analysis

            trend = (
                analysis
                .get("trend", {})
                .get("direction", "SIDEWAYS")
            )

            if trend == "BULLISH":

                bullish += 1

            elif trend == "BEARISH":

                bearish += 1

        overall = "SIDEWAYS"

        if bullish > bearish:

            overall = "BULLISH"

        elif bearish > bullish:

            overall = "BEARISH"

        return {

            "overall_trend": overall,

            "bullish_timeframes": bullish,

            "bearish_timeframes": bearish,

            "timeframes": results,

        }


multi_timeframe_analyzer = (
    MultiTimeframeAnalyzer()
)
