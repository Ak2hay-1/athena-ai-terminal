"""
Athena Trade Validator.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.models import AIRecommendation
from app.core.settings import settings


@dataclass(slots=True)
class TradeDecision:

    execute: bool

    reasons: list[str]


class TradeValidator:
    """
    Final validation before execution.
    """

    MIN_CONFIDENCE = 70

    MIN_CONFLUENCE = 60

    def validate(
        self,
        recommendation: AIRecommendation,
        *,
        news_context: dict | None = None,
    ) -> TradeDecision:

        reasons: list[str] = []
        execute = True

        if recommendation.signal in ("WAIT", "HOLD"):

            execute = False
            reasons.append(
                f"{recommendation.signal} signal."
            )

        if recommendation.confidence < self.MIN_CONFIDENCE:

            execute = False
            reasons.append(
                "Low confidence."
            )

        if (
            recommendation.confluence is not None
            and recommendation.confluence < self.MIN_CONFLUENCE
        ):

            execute = False
            reasons.append(
                "Low confluence."
            )

        if recommendation.risk_reward is not None and recommendation.risk_reward < 2:

            execute = False
            reasons.append(
                "Poor risk reward."
            )

        if news_context and news_context.get("high_impact_upcoming"):

            if recommendation.signal in ("BUY", "SELL"):
                execute = False
                reasons.append(
                    f"Blocked: high-impact news within {settings.NEWS_BLOCK_MINUTES} minutes."
                )

        if execute:
            reasons.append(
                "Trade approved."
            )

        return TradeDecision(
            execute=execute,
            reasons=reasons,
        )


trade_validator = TradeValidator()
