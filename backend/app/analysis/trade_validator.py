"""
Legacy trade validator wrapper.

Deprecated: institutional gates live in ``app.risk.trade_validator``.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

from app.ai.models import AIRecommendation
from app.core.settings import settings


@dataclass(slots=True)
class TradeDecision:
    execute: bool
    reasons: list[str]


class TradeValidator:
    """
    Legacy execution gate for order_manager compatibility.
    """

    @property
    def MIN_CONFIDENCE(self) -> int:  # noqa: N802
        return int(settings.MIN_AI_CONFIDENCE)

    @property
    def MIN_CONFLUENCE(self) -> int:  # noqa: N802
        return int(settings.MIN_CONFLUENCE_SCORE)

    def validate(
        self,
        recommendation: AIRecommendation,
        *,
        news_context: dict | None = None,
    ) -> TradeDecision:
        warnings.warn(
            "app.analysis.trade_validator is deprecated for signal generation; "
            "use app.risk.trade_validator",
            DeprecationWarning,
            stacklevel=2,
        )

        reasons: list[str] = []
        execute = True
        signal = recommendation.signal
        if hasattr(signal, "value"):
            signal = signal.value
        signal = str(signal)

        if signal in ("HOLD", "NO_TRADE", "WAIT"):
            execute = False
            reasons.append(f"{signal} signal.")

        if recommendation.confidence < self.MIN_CONFIDENCE:
            execute = False
            reasons.append("Low confidence.")

        if (
            recommendation.confluence is not None
            and recommendation.confluence < self.MIN_CONFLUENCE
        ):
            execute = False
            reasons.append("Low confluence.")

        if (
            recommendation.risk_reward is not None
            and recommendation.risk_reward < float(settings.MIN_RR)
        ):
            execute = False
            reasons.append("Poor risk reward.")

        if signal in ("BUY", "SELL"):
            entry = float(recommendation.entry or 0)
            stop = float(recommendation.stop_loss or 0)
            take = float(recommendation.take_profit or 0)
            if entry <= 0 or stop <= 0 or take <= 0:
                execute = False
                reasons.append("Invalid trade levels.")
            elif stop == entry or take == entry or stop == take:
                execute = False
                reasons.append("Collapsed stop loss / take profit.")
            elif signal == "BUY" and not (stop < entry < take):
                execute = False
                reasons.append("Invalid BUY levels (need SL < entry < TP).")
            elif signal == "SELL" and not (take < entry < stop):
                execute = False
                reasons.append("Invalid SELL levels (need TP < entry < SL).")

        if news_context and news_context.get("high_impact_upcoming"):
            if signal in ("BUY", "SELL"):
                execute = False
                reasons.append(
                    f"Blocked: high-impact news within {settings.NEWS_BLOCK_MINUTES} minutes."
                )

        if execute:
            reasons.append("Trade approved.")

        return TradeDecision(execute=execute, reasons=reasons)


trade_validator = TradeValidator()
