"""
Institutional trade probability from historical similarity + logistic model.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.settings import settings
from app.learning.signal_model import SignalModel
from app.learning.signal_model import feature_vector_from_recommendation
from app.models.learning import RecommendationOutcome
from app.models.recommendation import Recommendation
from app.schemas.probability import TradeProbabilityResult
from app.services.historical_similarity_service import HistoricalSimilarityService


TIMEFRAME_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
    "W1": 10080,
}


def classify_confidence_category(probability: int, *, low_sample: bool) -> str:
    if low_sample:
        return "LOW_SAMPLE"
    if probability >= 95:
        return "Exceptional"
    if probability >= 85:
        return "Very High"
    if probability >= 75:
        return "High"
    if probability >= 60:
        return "Moderate"
    if probability >= 40:
        return "Low"
    return "Very Low"


def format_hold_time(timeframe: str) -> str:
    minutes = TIMEFRAME_MINUTES.get(timeframe.upper(), 5)
    total_minutes = minutes * int(settings.LEARNING_OUTCOME_HORIZON_CANDLES)
    hours = total_minutes / 60.0
    if hours < 1:
        return f"{total_minutes:.0f} Minutes"
    return f"{hours:.1f} Hours"


class TradeProbabilityService:
    """
    Deterministic success probability estimator.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.similarity = HistoricalSimilarityService(db)
        self.signal_model = SignalModel(db)

    def estimate(
        self,
        recommendation: Recommendation | Any,
        *,
        analysis: dict[str, Any] | None = None,
        similar_rows: list[
            tuple[Recommendation, float, RecommendationOutcome | None]
        ]
        | None = None,
    ) -> TradeProbabilityResult:
        if not settings.LEARNING_ENABLED:
            return TradeProbabilityResult(
                confidence_category="LOW_SAMPLE",
                expected_hold_time=format_hold_time(
                    str(getattr(recommendation, "timeframe", "M5")),
                ),
            )

        rows = similar_rows
        if rows is None:
            rows = self.similarity.find_similar(
                recommendation,
                analysis=analysis,
                labeled_only=True,
            )

        outcomes = [o for _, _, o in rows if o is not None]
        n = len(outcomes)
        low_sample = n < int(settings.PROBABILITY_LOW_SAMPLE)

        wins = sum(1 for o in outcomes if o.label == "WIN")
        # Laplace smoothing
        historical_win_rate = int(round(100.0 * (wins + 1) / (n + 2))) if n else 0
        raw_win_rate = int(round(100.0 * wins / n)) if n else 0

        profits = [float(o.pnl_proxy) for o in outcomes if float(o.pnl_proxy) > 0]
        losses = [abs(float(o.pnl_proxy)) for o in outcomes if float(o.pnl_proxy) < 0]
        avg_profit = sum(profits) / len(profits) if profits else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0

        rr_values = [
            float(rec.risk_reward or 0)
            for rec, _, _ in rows
            if float(rec.risk_reward or 0) > 0
        ]
        expected_rr = sum(rr_values) / len(rr_values) if rr_values else float(
            getattr(recommendation, "risk_reward", 0) or 0
        )

        similar_prob = historical_win_rate
        blended = float(similar_prob)

        symbol = str(getattr(recommendation, "symbol", "") or "")
        timeframe = str(getattr(recommendation, "timeframe", "") or "")
        if (
            n >= int(settings.PROBABILITY_BLEND_MIN)
            and self.signal_model.has_model(symbol, timeframe)
        ):
            features = feature_vector_from_recommendation(
                recommendation if isinstance(recommendation, Recommendation) else None,
                analysis=analysis or getattr(recommendation, "analysis", None),
                confluence=getattr(recommendation, "confluence", None),
            )
            lr_score = self.signal_model.predict_score(symbol, timeframe, features)
            blended = 0.7 * (similar_prob / 100.0) + 0.3 * lr_score
            blended = blended * 100.0
            logger.debug(
                "Probability blend similar=%s lr=%.3f -> %.1f",
                similar_prob,
                lr_score,
                blended,
            )

        probability = int(round(max(0.0, min(100.0, blended))))
        category = classify_confidence_category(probability, low_sample=low_sample)

        return TradeProbabilityResult(
            probability=probability,
            confidence_category=category,
            similar_trades=n,
            historical_win_rate=raw_win_rate if n else 0,
            expected_rr=round(expected_rr, 2),
            expected_hold_time=format_hold_time(timeframe),
            historical_average_profit=round(avg_profit, 4),
            historical_average_loss=round(avg_loss, 4),
        )
