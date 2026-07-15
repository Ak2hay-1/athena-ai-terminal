"""
Athena Market Analyzer.

Converts raw OHLCV candles into a structured market analysis
consumed by the AI engine.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.indicator_engine import indicator_engine
from app.patterns.pattern_engine import pattern_engine


class MarketAnalyzer:

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict:

        if dataframe.empty:

            return {}

        df = dataframe.copy()

        # -----------------------------------------------------
        # Indicators
        # -----------------------------------------------------

        df = indicator_engine.calculate(df)

        # -----------------------------------------------------
        # Smart Money Concepts
        # -----------------------------------------------------

        df = pattern_engine.detect(df)

        latest = df.iloc[-1]

        return {

            "price": float(latest["close"]),

            "trend": latest.get(
                "trend",
                "SIDEWAYS",
            ),

            "ema9": float(latest["ema_9"]),

            "ema20": float(latest["ema_20"]),

            "ema50": float(latest["ema_50"]),

            "ema200": float(latest["ema_200"]),

            "rsi": float(latest["rsi_14"]),

            "macd": float(latest["macd"]),

            "macd_signal": float(
                latest["macd_signal"]
            ),

            "atr": float(
                latest["atr_14"]
            ),

            "bos": bool(
                latest.get("bos", False)
            ),

            "bos_direction": latest.get(
                "bos_direction"
            ),

            "choch": bool(
                latest.get("choch", False)
            ),

            "choch_direction": latest.get(
                "choch_direction"
            ),

            "order_block": bool(
                latest.get(
                    "order_block",
                    False,
                )
            ),

            "order_block_direction": latest.get(
                "ob_direction"
            ),

            "fvg": bool(
                latest.get(
                    "fvg",
                    False,
                )
            ),

            "fvg_direction": latest.get(
                "fvg_direction"
            ),

            "premium": bool(
                latest.get(
                    "premium",
                    False,
                )
            ),

            "discount": bool(
                latest.get(
                    "discount",
                    False,
                )
            ),

            "equal_high": bool(
                latest.get(
                    "equal_high",
                    False,
                )
            ),

            "equal_low": bool(
                latest.get(
                    "equal_low",
                    False,
                )
            ),

            "buy_liquidity": bool(
                latest.get(
                    "buy_liquidity",
                    False,
                )
            ),

            "sell_liquidity": bool(
                latest.get(
                    "sell_liquidity",
                    False,
                )
            ),

            "volume": int(
                latest["tick_volume"]
            ),

            "candles": len(df),
        }


market_analyzer = MarketAnalyzer()
