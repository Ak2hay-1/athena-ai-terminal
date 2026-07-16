"""
Athena Order Manager.

Central trade execution entry point.
"""

from __future__ import annotations

from app.ai.models import AIRecommendation
from app.core.logger import logger
from app.core.settings import settings
from app.analysis.trade_validator import trade_validator
from app.trading.paper_execution import paper_execution


class OrderManager:
    """
    Order Manager.

    Chooses execution provider and validates every trade.
    """

    def __init__(self):

        self.execution = paper_execution
        self._mt5_execution = None

        provider = getattr(
            settings,
            "EXECUTION_PROVIDER",
            "paper",
        ).lower()

        if provider == "mt5":
            from app.trading.mt5_execution import mt5_execution

            self.execution = mt5_execution
            self._mt5_execution = mt5_execution

        logger.info(
            "Execution Provider: %s",
            provider,
        )

    def execute(
        self,
        recommendation: AIRecommendation,
    ) -> dict:

        decision = trade_validator.validate(
            recommendation,
        )

        if not decision.execute:

            return {
                "success": False,
                "reasons": decision.reasons,
            }

        trade = self.execution.execute(
            recommendation,
        )

        return {
            "success": True,
            "trade": trade,
            "validation": decision.reasons,
        }

    def close(
        self,
        ticket: int,
    ) -> bool:

        return self.execution.close(
            ticket,
        )

    def positions(
        self,
    ):

        return self.execution.positions()


order_manager = OrderManager()
