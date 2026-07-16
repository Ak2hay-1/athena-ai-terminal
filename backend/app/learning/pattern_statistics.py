"""
Pattern success statistics.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.learning_repository import LearningRepository


class PatternStatistics:
    """
    Aggregate pattern win rates from stored occurrences.
    """

    def __init__(self, db: Session) -> None:
        self.repository = LearningRepository(db)

    def win_rates(
        self,
        symbol: str,
        timeframe: str,
    ) -> dict[str, float]:
        return self.repository.pattern_win_rates(
            symbol,
            timeframe,
        )
