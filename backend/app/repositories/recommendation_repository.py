"""
Recommendation Repository.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete
from sqlalchemy import desc
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import RecommendationSignal
from app.models.recommendation import Recommendation
from app.repositories.base_repository import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    """
    Repository for Recommendation model.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(
            db=db,
            model=Recommendation,
        )

    def get_latest(
        self,
        symbol: str,
        timeframe: str,
    ) -> Recommendation | None:
        """
        Get latest recommendation.
        """

        stmt = (
            select(Recommendation)
            .where(
                Recommendation.symbol == symbol,
                Recommendation.timeframe == timeframe,
            )
            .order_by(
                desc(Recommendation.created_at)
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def get_latest_signal(
        self,
        symbol: str,
        timeframe: str,
    ) -> Recommendation | None:
        """
        Return the latest actionable recommendation.
        """

        stmt = (
            select(Recommendation)
            .where(
                Recommendation.symbol == symbol,
                Recommendation.timeframe == timeframe,
                Recommendation.signal != RecommendationSignal.HOLD,
            )
            .order_by(
                desc(Recommendation.created_at)
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def get_history(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Recommendation]:
        """
        Recommendation history.
        """

        stmt = (
            select(Recommendation)
            .where(
                Recommendation.symbol == symbol,
                Recommendation.timeframe == timeframe,
            )
            .order_by(
                desc(Recommendation.created_at)
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def create_recommendation(
        self,
        recommendation,
        analysis: dict,
    ) -> Recommendation:
        """
        Create and persist a Recommendation model from
        an AI recommendation object.
        """

        db_recommendation = Recommendation(
            symbol=recommendation.symbol,
            timeframe=recommendation.timeframe,
            signal=recommendation.signal,
            confidence=int(recommendation.confidence),
            trend=recommendation.trend,
            confluence=recommendation.confluence,
            entry_price=recommendation.entry,
            stop_loss=recommendation.stop_loss,
            take_profit=recommendation.take_profit,
            risk_reward=recommendation.risk_reward,
            analysis=analysis,
            reasoning=recommendation.reason,
        )

        self.create(
            db_recommendation,
        )

        self.flush()

        return db_recommendation

    def delete_before(
        self,
        before: datetime,
    ) -> int:
        """
        Delete recommendations older than a timestamp.
        """

        stmt = (
            delete(Recommendation)
            .where(
                Recommendation.created_at < before
            )
        )

        result = self.db.execute(stmt)

        return result.rowcount or 0
