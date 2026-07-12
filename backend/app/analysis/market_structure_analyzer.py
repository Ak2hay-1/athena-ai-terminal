"""
Market Structure Analyzer.

Analyzes Smart Money Concepts and produces
a Market Structure Score.
"""

from __future__ import annotations

import pandas as pd


class MarketStructureAnalyzer:
    """
    Market Structure Analysis.
    """

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict:

        if dataframe.empty:

            return {
                "bias": "Unknown",
                "score": 0,
            }

        row = dataframe.iloc[-1]

        score = 0

        signals = {
            "bos": bool(row.get("bos", False)),
            "choch": bool(row.get("choch", False)),
            "fvg": bool(row.get("fvg", False)),
            "order_block": bool(row.get("order_block", False)),
            "buy_side_liquidity": bool(
                row.get("buy_side_liquidity", False)
            ),
            "sell_side_liquidity": bool(
                row.get("sell_side_liquidity", False)
            ),
            "buy_side_sweep": bool(
                row.get("buy_side_sweep", False)
            ),
            "sell_side_sweep": bool(
                row.get("sell_side_sweep", False)
            ),
        }

        # -----------------------------------
        # BOS
        # -----------------------------------

        if signals["bos"]:

            direction = row.get(
                "bos_direction",
                "",
            )

            if direction == "bullish":
                score += 25

            elif direction == "bearish":
                score -= 25

        # -----------------------------------
        # CHOCH
        # -----------------------------------

        if signals["choch"]:

            direction = row.get(
                "choch_direction",
                "",
            )

            if direction == "bullish":
                score += 20

            elif direction == "bearish":
                score -= 20

        # -----------------------------------
        # Fair Value Gap
        # -----------------------------------

        if signals["fvg"]:

            direction = row.get(
                "fvg_direction",
                "",
            )

            if direction == "bullish":
                score += 15

            elif direction == "bearish":
                score -= 15

        # -----------------------------------
        # Order Block
        # -----------------------------------

        if signals["order_block"]:

            direction = row.get(
                "order_block_type",
                "",
            )

            if direction == "bullish":
                score += 20

            elif direction == "bearish":
                score -= 20

        # -----------------------------------
        # Liquidity Sweep
        # -----------------------------------

        if signals["buy_side_sweep"]:
            score -= 10

        if signals["sell_side_sweep"]:
            score += 10

        # Clamp

        score = max(-100, min(score, 100))

        # Bias

        if score >= 50:

            bias = "Strong Bullish"

        elif score >= 20:

            bias = "Bullish"

        elif score <= -50:

            bias = "Strong Bearish"

        elif score <= -20:

            bias = "Bearish"

        else:

            bias = "Neutral"

        return {
            "bias": bias,
            "score": score,
            "signals": signals,
        }


market_structure_analyzer = MarketStructureAnalyzer()