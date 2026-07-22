"""
Athena Order Manager.

Central trade execution entry point — MT5 only.
"""

from __future__ import annotations

from typing import Literal

from app.ai.models import AIRecommendation
from app.analysis.trade_validator import trade_validator
from app.core.enums import RecommendationSignal
from app.core.logger import logger
from app.core.settings import settings
from app.trading.mt5_execution import mt5_execution


def _normalize_signal(recommendation: AIRecommendation) -> str:
    signal = recommendation.signal
    if hasattr(signal, "value"):
        signal = signal.value
    signal = str(signal).upper()

    if signal == "STRONG_BUY":
        recommendation.signal = RecommendationSignal.BUY
        return "BUY"
    if signal == "STRONG_SELL":
        recommendation.signal = RecommendationSignal.SELL
        return "SELL"
    return signal


def _validate_levels(signal: str, recommendation: AIRecommendation) -> list[str]:
    reasons: list[str] = []
    entry = float(recommendation.entry or 0)
    stop = float(recommendation.stop_loss or 0)
    take = float(recommendation.take_profit or 0)

    if entry <= 0 or stop <= 0 or take <= 0:
        reasons.append("Invalid trade levels.")
    elif stop == entry or take == entry or stop == take:
        reasons.append("Collapsed stop loss / take profit.")
    elif signal == "BUY" and not (stop < entry < take):
        reasons.append("Invalid BUY levels (need SL < entry < TP).")
    elif signal == "SELL" and not (take < entry < stop):
        reasons.append("Invalid SELL levels (need TP < entry < SL).")
    return reasons


class OrderManager:
    """
    Order Manager.

    Validates every trade and executes on MetaTrader 5.
    """

    def __init__(self):
        configured = getattr(settings, "EXECUTION_PROVIDER", "mt5").lower()
        if configured != "mt5":
            logger.error(
                "EXECUTION_PROVIDER=%s is not supported; Athena executes on MT5 only. "
                "Set EXECUTION_PROVIDER=mt5.",
                configured,
            )
        self._provider = "mt5"
        self.execution = mt5_execution
        self._mt5_execution = mt5_execution
        logger.info("Execution Provider: %s", self._provider)

    @property
    def provider(self) -> str:
        return self._provider

    def execute(
        self,
        recommendation: AIRecommendation,
        *,
        volume: float | None = None,
        user_id: int | None = None,
        source: Literal["manual", "auto"] = "manual",
    ) -> dict:
        del user_id  # MT5 path does not scope by Athena user id
        lot = (
            float(volume)
            if volume is not None and volume > 0
            else float(settings.DEFAULT_VOLUME)
        )

        if source == "manual":
            signal = _normalize_signal(recommendation)
            if signal in ("HOLD", "NO_TRADE", "WAIT", "NEUTRAL"):
                return {
                    "success": False,
                    "reasons": [f"{signal} signal — cannot open trade."],
                }
            if signal not in ("BUY", "SELL"):
                return {
                    "success": False,
                    "reasons": [f"Unsupported signal {signal}."],
                }
            level_reasons = _validate_levels(signal, recommendation)
            if level_reasons:
                return {"success": False, "reasons": level_reasons}
            validation_notes = ["Manual trade accepted."]
        else:
            decision = trade_validator.validate(recommendation)
            if not decision.execute:
                return {
                    "success": False,
                    "reasons": decision.reasons,
                }
            validation_notes = list(decision.reasons)

        try:
            trade = self.execution.execute(recommendation, volume=lot)
        except Exception as exc:
            logger.exception("MT5 execution failed")
            return {"success": False, "reasons": [str(exc)]}
        return {
            "success": True,
            "trade": trade,
            "validation": validation_notes,
        }

    def close(
        self,
        ticket: int,
        *,
        user_id: int | None = None,
    ) -> bool:
        del user_id
        return self.execution.close(ticket)

    def positions(self, *, user_id: int | None = None):
        del user_id
        return self.execution.positions()


order_manager = OrderManager()
