"""
Institutional trade quality score (0–100) and grade.
"""

from __future__ import annotations

from typing import Any

from app.schemas.probability import TradeProbabilityResult
from app.schemas.probability import TradeQualityResult


def classify_quality_grade(score: int) -> str:
    if score >= 95:
        return "Institutional"
    if score >= 90:
        return "A+"
    if score >= 85:
        return "A"
    if score >= 80:
        return "B+"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    return "D"


class TradeQualityService:
    """
    Composite quality from breakdown, heatmap, RR, probability, history.
    """

    def score(
        self,
        recommendation: Any,
        probability: TradeProbabilityResult,
        *,
        analysis: dict[str, Any] | None = None,
    ) -> TradeQualityResult:
        breakdown = getattr(recommendation, "confidence_breakdown", None)
        if hasattr(breakdown, "model_dump"):
            breakdown = breakdown.model_dump()
        if not isinstance(breakdown, dict):
            breakdown = {}

        heatmap = getattr(recommendation, "market_heatmap", None)
        if hasattr(heatmap, "model_dump"):
            heatmap = heatmap.model_dump()
        if not isinstance(heatmap, dict):
            heatmap = {}

        def cat_pct(name: str, default_max: float) -> float:
            if heatmap.get(name) is not None:
                return max(0.0, min(100.0, float(heatmap[name])))
            score = float(breakdown.get(name, 0) or 0)
            max_v = float(breakdown.get(f"{name}_max", default_max) or default_max) or default_max
            return max(0.0, min(100.0, 100.0 * score / max_v))

        trend = cat_pct("trend", 35)
        structure = cat_pct("structure", 20)
        momentum = cat_pct("momentum", 15)
        liquidity = cat_pct("liquidity", 15)
        risk = cat_pct("risk", 5)

        rr = float(getattr(recommendation, "risk_reward", 0) or 0)
        rr_score = max(0.0, min(100.0, (rr / 3.0) * 100.0))

        confidence = float(getattr(recommendation, "confidence", 0) or 0)
        prob = float(probability.probability)
        hist = float(probability.historical_win_rate)

        # Low-sample dampens historical contribution
        hist_weight = 0.05 if probability.confidence_category == "LOW_SAMPLE" else 0.12

        composite = (
            0.14 * trend
            + 0.14 * structure
            + 0.10 * momentum
            + 0.10 * liquidity
            + 0.08 * risk
            + 0.12 * rr_score
            + 0.12 * confidence
            + 0.08 * prob
            + hist_weight * hist
        )
        # Normalize remaining weight if hist_weight reduced
        if hist_weight < 0.12:
            composite = composite / (1.0 - (0.12 - hist_weight))

        trade_quality = int(round(max(0.0, min(100.0, composite))))
        return TradeQualityResult(
            trade_quality=trade_quality,
            grade=classify_quality_grade(trade_quality),
        )


trade_quality_service = TradeQualityService()
