"""
Confluence Analyzer.

Combines all analysis engines into a single market score.
"""

from __future__ import annotations


class ConfluenceAnalyzer:
    """
    Calculates an overall confluence score.
    """

    def analyze(
        self,
        trend: dict,
        momentum: dict,
        volatility: dict,
        market_structure: dict,
    ) -> dict:

        score = 0

        details = {}

        # -----------------------------------------
        # Trend (40%)
        # -----------------------------------------

        trend_score = trend.get("strength", 0)

        if trend.get("trend") in (
            "Bullish",
            "Strong Bullish",
        ):
            score += trend_score * 0.40

        elif trend.get("trend") in (
            "Bearish",
            "Strong Bearish",
        ):
            score -= trend_score * 0.40

        details["trend"] = trend_score

        # -----------------------------------------
        # Momentum (25%)
        # -----------------------------------------

        momentum_score = momentum.get("score", 0)

        score += momentum_score * 0.25

        details["momentum"] = momentum_score

        # -----------------------------------------
        # Market Structure (25%)
        # -----------------------------------------

        structure_score = market_structure.get(
            "score",
            0,
        )

        score += structure_score * 0.25

        details["market_structure"] = structure_score

        # -----------------------------------------
        # Volatility (10%)
        # -----------------------------------------

        volatility_score = volatility.get(
            "score",
            0,
        )

        if volatility.get("level") == "Medium":

            score += 10

        elif volatility.get("level") == "High":

            score += 5

        elif volatility.get("level") == "Extreme":

            score -= 15

        details["volatility"] = volatility_score

        score = round(score, 2)

        score = max(-100, min(score, 100))

        if score >= 70:

            recommendation = "STRONG BUY"

        elif score >= 40:

            recommendation = "BUY"

        elif score <= -70:

            recommendation = "STRONG SELL"

        elif score <= -40:

            recommendation = "SELL"

        else:

            recommendation = "WAIT"

        confidence = abs(score)

        return {

            "score": score,

            "confidence": confidence,

            "recommendation": recommendation,

            "details": details,
        }


confluence_analyzer = ConfluenceAnalyzer()