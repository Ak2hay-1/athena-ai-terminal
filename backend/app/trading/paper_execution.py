"""
Paper Trading Execution Provider.
"""

from __future__ import annotations

from app.ai.models import AIRecommendation


class PaperExecutionProvider:
    """
    In-memory paper trading backend.
    """

    def __init__(self) -> None:

        self._ticket = 1
        self._positions: list[dict] = []

    def execute(
        self,
        recommendation: AIRecommendation,
    ) -> dict:

        trade = {
            "ticket": self._ticket,
            "symbol": recommendation.symbol,
            "signal": recommendation.signal,
            "entry": recommendation.entry,
            "stop_loss": recommendation.stop_loss,
            "take_profit": recommendation.take_profit,
            "volume": 1.0,
            "status": "OPEN",
        }

        self._positions.append(trade)
        self._ticket += 1
        return trade

    def close(
        self,
        ticket: int,
    ) -> bool:

        for position in self._positions:

            if position["ticket"] == ticket:
                position["status"] = "CLOSED"
                return True

        return False

    def positions(
        self,
    ) -> list:

        return [
            position
            for position in self._positions
            if position["status"] == "OPEN"
        ]


paper_execution = PaperExecutionProvider()
