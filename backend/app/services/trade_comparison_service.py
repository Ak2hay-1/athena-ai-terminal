"""
Deterministic recommendation comparison engine.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.probability import MetricComparison
from app.schemas.probability import TradeComparisonResult
from app.schemas.probability import TradeProbabilityResult
from app.services.trade_probability_service import TradeProbabilityService
from app.services.trade_quality_service import TradeQualityService


def _structure_label(rec: Recommendation) -> str:
    validation = rec.validation or {}
    if hasattr(validation, "model_dump"):
        validation = validation.model_dump()
    if not isinstance(validation, dict):
        validation = {}
    score = sum(
        1
        for key in ("bos", "choch", "liquidity", "structure_sl")
        if validation.get(key)
    )
    if score >= 3:
        return "Excellent"
    if score >= 2:
        return "Average"
    if score >= 1:
        return "Weak"
    return "Poor"


def _liquidity_label(rec: Recommendation) -> str:
    validation = rec.validation or {}
    if hasattr(validation, "model_dump"):
        validation = validation.model_dump()
    if not isinstance(validation, dict):
        validation = {}
    heatmap = rec.market_heatmap or {}
    if hasattr(heatmap, "model_dump"):
        heatmap = heatmap.model_dump()
    if not isinstance(heatmap, dict):
        heatmap = {}
    if validation.get("liquidity") or float(heatmap.get("liquidity") or 0) >= 70:
        return "Strong"
    if float(heatmap.get("liquidity") or 0) >= 40:
        return "Average"
    return "Weak"


def _news_label(rec: Recommendation) -> str:
    validation = rec.validation or {}
    if hasattr(validation, "model_dump"):
        validation = validation.model_dump()
    if not isinstance(validation, dict):
        validation = {}
    if validation.get("news"):
        return "Neutral"
    return "High Impact"


def _trend_str(rec: Recommendation) -> str:
    trend = rec.trend
    if hasattr(trend, "value"):
        trend = trend.value
    value = str(trend or "").upper()
    if value == "BULLISH":
        return "Bullish"
    if value == "BEARISH":
        return "Bearish"
    return "Neutral"


class TradeComparisonService:
    """
    Compare two recommendations side by side.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RecommendationRepository(db)
        self.probability_service = TradeProbabilityService(db)
        self.quality_service = TradeQualityService()

    def compare(
        self,
        recommendation_a: Recommendation,
        recommendation_b: Recommendation,
    ) -> TradeComparisonResult:
        prob_a = self._probability(recommendation_a)
        prob_b = self._probability(recommendation_b)
        qual_a = self._quality(recommendation_a, prob_a)
        qual_b = self._quality(recommendation_b, prob_b)

        comparison: dict[str, MetricComparison] = {
            "confidence": self._numeric_metric(
                int(recommendation_a.confidence),
                int(recommendation_b.confidence),
            ),
            "probability": self._numeric_metric(
                prob_a.probability,
                prob_b.probability,
            ),
            "trend": MetricComparison(
                a=_trend_str(recommendation_a),
                b=_trend_str(recommendation_b),
                winner=None,
            ),
            "rr": self._numeric_metric(
                float(recommendation_a.risk_reward or 0),
                float(recommendation_b.risk_reward or 0),
            ),
            "structure": MetricComparison(
                a=_structure_label(recommendation_a),
                b=_structure_label(recommendation_b),
                winner=self._label_winner(
                    _structure_label(recommendation_a),
                    _structure_label(recommendation_b),
                    order=["Poor", "Weak", "Average", "Excellent"],
                ),
            ),
            "liquidity": MetricComparison(
                a=_liquidity_label(recommendation_a),
                b=_liquidity_label(recommendation_b),
                winner=self._label_winner(
                    _liquidity_label(recommendation_a),
                    _liquidity_label(recommendation_b),
                    order=["Weak", "Average", "Strong"],
                ),
            ),
            "news": MetricComparison(
                a=_news_label(recommendation_a),
                b=_news_label(recommendation_b),
                winner="A"
                if _news_label(recommendation_a) == "Neutral"
                and _news_label(recommendation_b) != "Neutral"
                else (
                    "B"
                    if _news_label(recommendation_b) == "Neutral"
                    and _news_label(recommendation_a) != "Neutral"
                    else None
                ),
            ),
            "quality": self._numeric_metric(qual_a, qual_b),
            "grade": MetricComparison(
                a=getattr(recommendation_a, "quality_grade", None)
                or self.quality_service.score(recommendation_a, prob_a).grade,
                b=getattr(recommendation_b, "quality_grade", None)
                or self.quality_service.score(recommendation_b, prob_b).grade,
                winner=None,
            ),
        }

        # Overall winner: quality → probability → confidence
        winner = "TIE"
        if qual_a != qual_b:
            winner = "A" if qual_a > qual_b else "B"
        elif prob_a.probability != prob_b.probability:
            winner = "A" if prob_a.probability > prob_b.probability else "B"
        elif int(recommendation_a.confidence) != int(recommendation_b.confidence):
            winner = (
                "A"
                if int(recommendation_a.confidence) > int(recommendation_b.confidence)
                else "B"
            )

        comparison["grade"].winner = winner if winner != "TIE" else None

        return TradeComparisonResult(winner=winner, comparison=comparison)

    def compare_ids(self, id_a: int, id_b: int) -> TradeComparisonResult | None:
        a = self.repo.read(id_a)
        b = self.repo.read(id_b)
        if a is None or b is None:
            return None
        return self.compare(a, b)

    def _probability(self, rec: Recommendation) -> TradeProbabilityResult:
        detail = getattr(rec, "probability_detail", None) or {}
        if isinstance(detail, dict) and detail.get("probability") is not None:
            return TradeProbabilityResult.model_validate(detail)
        if getattr(rec, "trade_probability", None):
            return TradeProbabilityResult(
                probability=int(rec.trade_probability or 0),
                similar_trades=int(getattr(rec, "similar_trade_count", 0) or 0),
                historical_win_rate=int(getattr(rec, "historical_win_rate", 0) or 0),
                expected_rr=float(getattr(rec, "expected_rr", 0) or 0),
                expected_hold_time=str(getattr(rec, "expected_hold_time", "") or ""),
            )
        return self.probability_service.estimate(rec)

    def _quality(self, rec: Recommendation, prob: TradeProbabilityResult) -> int:
        if getattr(rec, "trade_quality", None):
            return int(rec.trade_quality or 0)
        return self.quality_service.score(rec, prob).trade_quality

    @staticmethod
    def _numeric_metric(a: float | int, b: float | int) -> MetricComparison:
        winner = None
        if a > b:
            winner = "A"
        elif b > a:
            winner = "B"
        return MetricComparison(a=a, b=b, winner=winner)

    @staticmethod
    def _label_winner(a: str, b: str, order: list[str]) -> str | None:
        try:
            ia = order.index(a)
            ib = order.index(b)
        except ValueError:
            return None
        if ia > ib:
            return "A"
        if ib > ia:
            return "B"
        return None
