"""
Learning orchestration service.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.learning.adaptive_weights import AdaptiveWeightEngine
from app.learning.pattern_statistics import PatternStatistics
from app.learning.signal_model import SignalModel
from app.models.learning import RecommendationOutcome
from app.repositories.learning_repository import LearningRepository
from app.services.base_service import BaseService
from app.services.learning.adaptive_weight_service import AdaptiveWeightService
from app.services.learning.calibration_service import CalibrationService
from app.services.learning.feature_analytics_service import FeatureAnalyticsService
from app.services.learning.outcome_tracker import OutcomeTracker
from app.services.learning.regime_analytics_service import RegimeAnalyticsService
from app.services.learning.strategy_analytics_service import StrategyAnalyticsService
from app.services.learning.symbol_analytics_service import SymbolAnalyticsService
from app.services.learning.timeframe_analytics_service import TimeframeAnalyticsService


class LearningService(BaseService):
    """Coordinate outcome labeling, analytics, weights, and retraining."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.tracker = OutcomeTracker(db)
        self.stats = PatternStatistics(db)
        self.weights = AdaptiveWeightEngine(db)
        self.confidence_weights = AdaptiveWeightService(db)
        self.model = SignalModel(db)
        self.features = FeatureAnalyticsService(db)
        self.symbols = SymbolAnalyticsService(db)
        self.timeframes = TimeframeAnalyticsService(db)
        self.strategies = StrategyAnalyticsService(db)
        self.regimes = RegimeAnalyticsService(db)
        self.calibration = CalibrationService(db)

    def run_labeling(self) -> int:
        count = self.tracker.label_pending()
        self.weights.clear_cache()
        return count

    def refresh_analytics(self) -> dict[str, int]:
        return {
            "features": self.features.refresh(),
            "symbols": self.symbols.refresh(),
            "timeframes": self.timeframes.refresh(),
            "strategies": self.strategies.refresh(),
            "regimes": self.regimes.refresh(),
            "calibration": self.calibration.refresh(),
        }

    def update_confidence_weights(self, *, reason: str = "scheduled") -> dict | None:
        history = self.confidence_weights.update_weights(reason=reason)
        if history is None:
            return None
        return {
            "version": history.version,
            "learning_version": history.learning_version,
            "weights": history.weights,
            "reason": history.reason,
        }

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
            "confidence_weights": self.confidence_weights.get_active_weights(),
            "weight_version": self.confidence_weights.get_active_version(),
            "sample_size": repo.count_outcomes(
                symbol,
                timeframe,
            ),
            "model_accuracy": latest.accuracy if latest else None,
            "model_version": latest.model_version if latest else None,
        }

    def get_dashboard(self) -> dict:
        outcomes = self.db.query(RecommendationOutcome).all()
        wins = sum(1 for o in outcomes if o.label == "WIN")
        losses = sum(1 for o in outcomes if o.label == "LOSS")
        sample = len(outcomes)
        win_rate = round(100.0 * wins / sample, 2) if sample else 0.0
        profits = [
            o.profit if o.profit is not None else o.pnl_proxy for o in outcomes
        ]
        gains = sum(p for p in profits if p and p > 0)
        loss_sum = sum(abs(p) for p in profits if p and p < 0)
        profit_factor = round(gains / loss_sum, 4) if loss_sum else round(gains, 4)

        return {
            "sample_size": sample,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "weight_version": self.confidence_weights.get_active_version(),
            "learning_version": settings.LEARNING_SYSTEM_VERSION,
            "features": [r.to_dict() for r in self.features.list_all()],
            "symbols": [r.to_dict() for r in self.symbols.list_all()],
            "timeframes": [r.to_dict() for r in self.timeframes.list_all()],
            "regimes": [r.to_dict() for r in self.regimes.list_all()],
            "strategies": [r.to_dict() for r in self.strategies.list_all()],
            "calibration": [r.to_dict() for r in self.calibration.list_all()],
            "weights": self.confidence_weights.get_active_weights(),
        }
