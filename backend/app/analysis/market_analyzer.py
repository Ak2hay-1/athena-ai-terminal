"""
Athena Market Analyzer.

Builds a structured market context for the AI.
"""

from __future__ import annotations

import pandas as pd

from app.analysis.confluence_engine import confluence_engine
from app.indicators.indicator_engine import indicator_engine
from app.patterns.pattern_engine import pattern_engine


class MarketAnalyzer:
    """
    Main market analysis pipeline.
    """

    def analyze(
        self,
        dataframe: pd.DataFrame,
        *,
        news_context: dict | None = None,
        multi_timeframe: dict | None = None,
        weights: dict[str, float] | None = None,
    ) -> dict:

        if dataframe.empty:
            return {}

        df = dataframe.copy()

        df = indicator_engine.calculate(df)
        df = pattern_engine.detect(df)

        confluence = confluence_engine.analyze(
            df,
            news_context=news_context,
            weights=weights,
        )

        latest = df.iloc[-1]

        analysis = {
            "market": {
                "price": float(latest["close"]),
                "volume": int(latest["tick_volume"]),
                "candles": len(df),
            },
            "trend": {
                "direction": latest.get(
                    "trend",
                    "SIDEWAYS",
                ),
                "bullish": bool(
                    latest.get("trend") == "BULLISH"
                ),
                "bearish": bool(
                    latest.get("trend") == "BEARISH"
                ),
            },
            "indicators": {
                "ema": {
                    "ema9": float(latest["ema_9"]),
                    "ema20": float(latest["ema_20"]),
                    "ema50": float(latest["ema_50"]),
                    "ema200": float(latest["ema_200"]),
                },
                "rsi": float(latest["rsi_14"]),
                "macd": {
                    "value": float(latest["macd"]),
                    "signal": float(
                        latest["macd_signal"]
                    ),
                    "bullish": bool(
                        latest["macd_bullish"]
                    ),
                },
                "atr": float(
                    latest["atr_14"]
                ),
            },
            "smart_money": {
                "bos": {
                    "active": bool(
                        latest.get("bos")
                    ),
                    "direction": latest.get(
                        "bos_direction"
                    ),
                },
                "choch": {
                    "active": bool(
                        latest.get("choch")
                    ),
                    "direction": latest.get(
                        "choch_direction"
                    ),
                },
                "order_block": bool(
                    latest.get("order_block")
                ),
                "fair_value_gap": bool(
                    latest.get("fvg")
                ),
                "premium": bool(
                    latest.get("premium")
                ),
                "discount": bool(
                    latest.get("discount")
                ),
                "equal_high": bool(
                    latest.get("equal_high")
                ),
                "equal_low": bool(
                    latest.get("equal_low")
                ),
                "buy_liquidity": bool(
                    latest.get("buy_liquidity")
                ),
                "sell_liquidity": bool(
                    latest.get("sell_liquidity")
                ),
            },
            "confluence": confluence,
        }

        if news_context:
            analysis["news"] = news_context

        if multi_timeframe:
            analysis["multi_timeframe"] = multi_timeframe

        return analysis


market_analyzer = MarketAnalyzer()
