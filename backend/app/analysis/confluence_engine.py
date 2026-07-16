"""
Athena Confluence Engine.

Combines indicator and Smart Money Concept signals into
a single confluence score.
"""

from __future__ import annotations

import pandas as pd

from app.core.settings import settings


class ConfluenceEngine:

    def analyze(
        self,
        dataframe: pd.DataFrame,
        *,
        news_context: dict | None = None,
        weights: dict[str, float] | None = None,
    ) -> dict:

        latest = dataframe.iloc[-1]
        weights = weights or {}
        score = 0.0
        reasons: list[str] = []

        def add(points: float, reason: str, key: str) -> None:
            nonlocal score
            multiplier = weights.get(key, 1.0)
            score += points * multiplier
            reasons.append(reason)

        if latest["ema_9"] > latest["ema_20"]:
            add(10, "EMA9 above EMA20", "ema")

        if latest["ema_20"] > latest["ema_50"]:
            add(10, "EMA20 above EMA50", "ema")

        if 50 <= latest["rsi_14"] <= 70:
            add(10, "Healthy bullish RSI", "rsi")
        elif 30 <= latest["rsi_14"] <= 50:
            add(-10, "Weak RSI", "rsi")

        if latest["macd_bullish"]:
            add(10, "Bullish MACD", "macd")
        else:
            add(-10, "Bearish MACD", "macd")

        if latest.get("bos"):
            add(20, f"BOS {latest['bos_direction']}", "bos")

        if latest.get("choch"):
            add(15, f"CHOCH {latest['choch_direction']}", "choch")

        if latest.get("fvg"):
            add(10, "Fair Value Gap", "fvg")

        if latest.get("order_block"):
            add(15, "Order Block", "order_block")

        if news_context:
            news_score = news_context.get("score", 0)
            weighted = news_score * (
                settings.NEWS_SENTIMENT_WEIGHT / 10
            ) * weights.get("news", 1.0)
            score += weighted
            reasons.append(
                f"News sentiment {news_context.get('sentiment', 'NEUTRAL')}"
            )

            if news_context.get("high_impact_upcoming"):
                score -= 20 * weights.get("news", 1.0)
                reasons.append(
                    "High-impact news window approaching"
                )

        score = max(0, min(int(score), 100))

        return {
            "score": score,
            "reasons": reasons,
            "bullish": score >= 60,
            "bearish": score <= 40,
        }


confluence_engine = ConfluenceEngine()
