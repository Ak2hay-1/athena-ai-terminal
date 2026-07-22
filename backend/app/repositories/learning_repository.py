"""
Learning data repository.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone

from sqlalchemy import desc
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.learning import ConfluenceSnapshot
from app.models.learning import ModelMetric
from app.models.learning import PatternOccurrence
from app.models.learning import RecommendationOutcome
from app.models.recommendation import Recommendation
from app.repositories.base_repository import BaseRepository


class LearningRepository(BaseRepository[RecommendationOutcome]):
    """
    Outcome and learning metrics persistence.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(db, RecommendationOutcome)

    def outcome_exists(
        self,
        recommendation_id: int,
    ) -> bool:
        return (
            self.db.query(RecommendationOutcome)
            .filter(
                RecommendationOutcome.recommendation_id
                == recommendation_id
            )
            .first()
            is not None
        )

    def get_unlabeled_recommendations(
        self,
        limit: int = 100,
    ) -> list[Recommendation]:
        labeled_subquery = (
            select(RecommendationOutcome.recommendation_id)
        )

        return (
            self.db.query(Recommendation)
            .filter(~Recommendation.id.in_(labeled_subquery))
            .order_by(desc(Recommendation.created_at))
            .limit(limit)
            .all()
        )

    def save_outcome(
        self,
        outcome: RecommendationOutcome,
    ) -> RecommendationOutcome:
        self.db.add(outcome)
        self.db.flush()
        return outcome

    def save_snapshot(
        self,
        snapshot: ConfluenceSnapshot,
    ) -> ConfluenceSnapshot:
        self.db.add(snapshot)
        self.db.flush()
        return snapshot

    def save_pattern(
        self,
        pattern: PatternOccurrence,
    ) -> PatternOccurrence:
        self.db.add(pattern)
        self.db.flush()
        return pattern

    def save_metric(
        self,
        metric: ModelMetric,
    ) -> ModelMetric:
        self.db.add(metric)
        self.db.flush()
        return metric

    def pattern_win_rates(
        self,
        symbol: str,
        timeframe: str,
    ) -> dict[str, float]:
        rows = (
            self.db.query(PatternOccurrence)
            .filter(
                PatternOccurrence.symbol == symbol.upper(),
                PatternOccurrence.timeframe == timeframe.upper(),
                PatternOccurrence.outcome.isnot(None),
            )
            .all()
        )

        stats: dict[str, list[str]] = {}

        for row in rows:
            stats.setdefault(row.pattern_type, []).append(row.outcome)

        result: dict[str, float] = {}

        for pattern, outcomes in stats.items():
            wins = sum(1 for o in outcomes if o == "WIN")
            result[pattern] = wins / len(outcomes) if outcomes else 0.0

        return result

    def latest_metric(
        self,
        symbol: str,
        timeframe: str,
    ) -> ModelMetric | None:
        return (
            self.db.query(ModelMetric)
            .filter(
                ModelMetric.symbol == symbol.upper(),
                ModelMetric.timeframe == timeframe.upper(),
            )
            .order_by(desc(ModelMetric.created_at))
            .first()
        )

    def count_outcomes(
        self,
        symbol: str,
        timeframe: str,
    ) -> int:
        return (
            self.db.query(RecommendationOutcome)
            .filter(
                RecommendationOutcome.symbol == symbol.upper(),
                RecommendationOutcome.timeframe == timeframe.upper(),
            )
            .count()
        )

    def list_outcomes(
        self,
        symbol: str | None = None,
        timeframe: str | None = None,
        limit: int = 500,
    ) -> list[RecommendationOutcome]:
        query = self.db.query(RecommendationOutcome)

        if symbol:
            query = query.filter(
                RecommendationOutcome.symbol == symbol.upper()
            )

        if timeframe:
            query = query.filter(
                RecommendationOutcome.timeframe == timeframe.upper()
            )

        return (
            query.order_by(desc(RecommendationOutcome.labeled_at))
            .limit(limit)
            .all()
        )

    def list_outcomes_with_recommendations(
        self,
        symbol: str | None = None,
        timeframe: str | None = None,
        limit: int = 5000,
    ) -> list[tuple[RecommendationOutcome, Recommendation | None]]:
        """
        Join outcomes to parent recommendations for feature extraction.
        """
        query = (
            self.db.query(RecommendationOutcome, Recommendation)
            .outerjoin(
                Recommendation,
                Recommendation.id == RecommendationOutcome.recommendation_id,
            )
        )

        if symbol:
            query = query.filter(
                RecommendationOutcome.symbol == symbol.upper()
            )

        if timeframe:
            query = query.filter(
                RecommendationOutcome.timeframe == timeframe.upper()
            )

        rows = (
            query.order_by(desc(RecommendationOutcome.labeled_at))
            .limit(limit)
            .all()
        )
        return [(outcome, recommendation) for outcome, recommendation in rows]

    def list_labeled_recommendations(
        self,
        symbol: str,
        timeframe: str,
        signal: str | None = None,
        limit: int = 500,
        exclude_id: int | None = None,
    ) -> list[tuple[Recommendation, RecommendationOutcome]]:
        """
        Recommendations that have outcomes, for similarity / probability.
        """
        query = (
            self.db.query(Recommendation, RecommendationOutcome)
            .join(
                RecommendationOutcome,
                RecommendationOutcome.recommendation_id == Recommendation.id,
            )
            .filter(
                Recommendation.symbol == symbol.upper(),
                Recommendation.timeframe == timeframe.upper(),
            )
        )

        if signal:
            from app.core.enums import RecommendationSignal

            try:
                signal_enum = RecommendationSignal(signal.upper())
                query = query.filter(Recommendation.signal == signal_enum)
            except ValueError:
                query = query.filter(Recommendation.signal == signal)

        if exclude_id is not None:
            query = query.filter(Recommendation.id != exclude_id)

        rows = (
            query.order_by(desc(Recommendation.created_at))
            .limit(limit)
            .all()
        )
        return [(rec, outcome) for rec, outcome in rows]
