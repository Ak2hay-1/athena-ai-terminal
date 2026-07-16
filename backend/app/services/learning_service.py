"""
Learning orchestration service.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.learning.adaptive_weights import AdaptiveWeightEngine
from app.learning.outcome_labeler import OutcomeLabeler
from app.learning.pattern_statistics import PatternStatistics
from app.learning.signal_model import SignalModel
from app.services.base_service import BaseService


class LearningService(BaseService):
    """
    Coordinate outcome labeling, stats, and retraining.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.labeler = OutcomeLabeler(db)
        self.stats = PatternStatistics(db)
        self.weights = AdaptiveWeightEngine(db)
        self.model = SignalModel(db)

    def run_labeling(self) -> int:
        count = self.labeler.label_pending()
        self.weights.clear_cache()
        return count

    def retrain_all(self) -> list[dict]:
        results = []

        if not settings.LEARNING_ENABLED:
            return results

        for symbol in settings.MARKET_SYMBOLS:
            for timeframe in settings.MARKET_TIMEFRAMES:
                metric = self.model.train(symbol, timeframe)

                if metric:
                    results.append(
                        {
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "accuracy": metric.accuracy,
                            "sample_size": metric.sample_size,
                        }
                    )

        self.commit()
        return results

    def get_stats(
        self,
        symbol: str,
        timeframe: str,
    ) -> dict:
        from app.repositories.learning_repository import LearningRepository

        repo = LearningRepository(self.db)
        latest = repo.latest_metric(symbol, timeframe)

        return {
            "pattern_win_rates": self.stats.win_rates(
                symbol,
                timeframe,
            ),
            "weights": self.weights.get_weights(
                symbol,
                timeframe,
            ),
            "sample_size": repo.count_outcomes(
                symbol,
                timeframe,
            ),
            "model_accuracy": latest.accuracy if latest else None,
            "model_version": latest.model_version if latest else None,
        }
