"""
Market Analyzer.

Combines:
- Indicators
- Smart Money Concepts
- Market Statistics

Returns a structured market analysis.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.indicator_engine import indicator_engine
from app.patterns.pattern_engine import pattern_engine


class MarketAnalyzer:
    """
    Main market analysis engine.
    """

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict:

        if dataframe.empty:
            return {
                "status": "error",
                "message": "No market data available."
            }

        # -----------------------------
        # Calculate Indicators
        # -----------------------------

        df = indicator_engine.calculate(dataframe)

        # -----------------------------
        # Detect Patterns
        # -----------------------------

        df = pattern_engine.detect(df)

        latest = df.iloc[-1]

        analysis = {

            "symbol": dataframe.iloc[-1].get("symbol", "UNKNOWN"),

            "time":

                str(latest["time"]),

            "price":

                float(latest["close"]),

            "trend":

                self._trend(latest),

            "momentum":

                self._momentum(latest),

            "volatility":

                self._volatility(latest),

            "market_structure":

                self._market_structure(latest),

            "smart_money":

                {

                    "bos":

                        bool(latest.get("bos", False)),

                    "choch":

                        bool(latest.get("choch", False)),

                    "fvg":

                        bool(latest.get("fvg", False)),

                    "order_block":

                        bool(
                            latest.get(
                                "order_block",
                                False,
                            )
                        ),

                    "liquidity":

                        bool(
                            latest.get(
                                "buy_side_liquidity",
                                False,
                            )
                            or
                            latest.get(
                                "sell_side_liquidity",
                                False,
                            )
                        ),
                },
        }

        return analysis

    # -----------------------------------------------------

    def _trend(
        self,
        row,
    ) -> str:

        if row["ema_20"] > row["ema_50"] > row["ema_200"]:
            return "Bullish"

        if row["ema_20"] < row["ema_50"] < row["ema_200"]:
            return "Bearish"

        return "Sideways"

    # -----------------------------------------------------

    def _momentum(
        self,
        row,
    ) -> str:

        if row["macd"] > row["macd_signal"]:
            return "Bullish"

        if row["macd"] < row["macd_signal"]:
            return "Bearish"

        return "Neutral"

    # -----------------------------------------------------

    def _volatility(
        self,
        row,
    ) -> str:

        atr = row["atr_14"]

        if atr > 15:
            return "High"

        if atr > 5:
            return "Medium"

        return "Low"

    # -----------------------------------------------------

    def _market_structure(
        self,
        row,
    ) -> str:

        if row.get("bos", False):
            return "Break of Structure"

        if row.get("choch", False):
            return "Change of Character"

        return "Range"


market_analyzer = MarketAnalyzer()