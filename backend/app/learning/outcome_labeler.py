"""
Outcome labeling for recommendations.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.learning import RecommendationOutcome
from app.repositories.learning_repository import LearningRepository
from app.repositories.market_repository import MarketRepository


class OutcomeLabeler:
    """
    Label past recommendations using subsequent price movement.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.learning = LearningRepository(db)
        self.market = MarketRepository(db)

    def label_pending(self) -> int:
        pending = self.learning.get_unlabeled_recommendations(limit=200)
        labeled = 0
        horizon = settings.LEARNING_OUTCOME_HORIZON_CANDLES

        for recommendation in pending:
            if self.learning.outcome_exists(recommendation.id):
                continue

            candles = self.market.get_latest_candles(
                recommendation.symbol,
                recommendation.timeframe,
                limit=horizon + 5,
            )

            if len(candles) < horizon + 1:
                continue

            entry = float(recommendation.entry or candles[-horizon].close)
            exit_price = float(candles[-1].close)
            signal = recommendation.signal.upper()

            if signal == "BUY":
                pnl = exit_price - entry
            elif signal == "SELL":
                pnl = entry - exit_price
            else:
                pnl = 0.0

            if pnl > 0:
                label = "WIN"
            elif pnl < 0:
                label = "LOSS"
            else:
                label = "NEUTRAL"

            outcome = RecommendationOutcome(
                recommendation_id=recommendation.id,
                symbol=recommendation.symbol,
                timeframe=recommendation.timeframe,
                predicted_signal=signal,
                label=label,
                pnl_proxy=pnl,
                horizon_candles=horizon,
                labeled_at=datetime.now(timezone.utc),
            )

            self.learning.save_outcome(outcome)
            labeled += 1

        self.db.commit()
        return labeled
