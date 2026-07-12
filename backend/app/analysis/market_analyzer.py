"""
Market Analyzer.

Main orchestration engine.
"""

from __future__ import annotations

import pandas as pd

from app.analysis.trend_analyzer import trend_analyzer
from app.indicators.indicator_engine import indicator_engine
from app.patterns.pattern_engine import pattern_engine


class MarketAnalyzer:

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict:

        if dataframe.empty:

            return {
                "status": "error",
                "message": "No market data.",
            }

        df = indicator_engine.calculate(dataframe)

        df = pattern_engine.detect(df)

        trend = trend_analyzer.analyze(df)

        latest = df.iloc[-1]

        return {

            "symbol": dataframe.iloc[-1].get(
                "symbol",
                "UNKNOWN",
            ),

            "price": float(latest["close"]),

            "trend": trend,

            "patterns": {

                "bos": bool(
                    latest.get("bos", False)
                ),

                "choch": bool(
                    latest.get("choch", False)
                ),

                "fvg": bool(
                    latest.get("fvg", False)
                ),

                "order_block": bool(
                    latest.get(
                        "order_block",
                        False,
                    )
                ),

                "liquidity": bool(
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


market_analyzer = MarketAnalyzer()