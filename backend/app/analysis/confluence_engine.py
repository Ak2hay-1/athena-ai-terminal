"""
Athena Confluence Engine.

Combines indicator and Smart Money Concept signals into
a single confluence score.
"""

from __future__ import annotations

import pandas as pd


class ConfluenceEngine:

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict:

        latest = dataframe.iloc[-1]

        score = 0

        reasons: list[str] = []

        # ==========================================
        # EMA
        # ==========================================

        if latest["ema_9"] > latest["ema_20"]:

            score += 10

            reasons.append(
                "EMA9 above EMA20"
            )

        if latest["ema_20"] > latest["ema_50"]:

            score += 10

            reasons.append(
                "EMA20 above EMA50"
            )

        # ==========================================
        # RSI
        # ==========================================

        if 50 <= latest["rsi_14"] <= 70:

            score += 10

            reasons.append(
                "Healthy bullish RSI"
            )

        elif 30 <= latest["rsi_14"] <= 50:

            score -= 10

            reasons.append(
                "Weak RSI"
            )

        # ==========================================
        # MACD
        # ==========================================

        if latest["macd_bullish"]:

            score += 10

            reasons.append(
                "Bullish MACD"
            )

        else:

            score -= 10

            reasons.append(
                "Bearish MACD"
            )

        # ==========================================
        # BOS
        # ==========================================

        if latest.get("bos"):

            score += 20

            reasons.append(
                f"BOS {latest['bos_direction']}"
            )

        # ==========================================
        # CHOCH
        # ==========================================

        if latest.get("choch"):

            score += 15

            reasons.append(
                f"CHOCH {latest['choch_direction']}"
            )

        # ==========================================
        # FVG
        # ==========================================

        if latest.get("fvg"):

            score += 10

            reasons.append(
                "Fair Value Gap"
            )

        # ==========================================
        # Order Block
        # ==========================================

        if latest.get("order_block"):

            score += 15

            reasons.append(
                "Order Block"
            )

        score = max(
            0,
            min(
                score,
                100,
            ),
        )

        return {

            "score": score,

            "reasons": reasons,

            "bullish": score >= 60,

            "bearish": score <= 40,

        }


confluence_engine = ConfluenceEngine()