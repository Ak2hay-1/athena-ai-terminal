"""
Historical similarity engine — weighted comparison of recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.settings import settings
from app.models.learning import RecommendationOutcome
from app.models.recommendation import Recommendation
from app.repositories.learning_repository import LearningRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.probability import SimilarRecommendationItem


@dataclass(slots=True)
class SimilarityFeatures:
    """Normalized features used for similarity scoring."""

    trend: float  # -1 bearish, 0 sideways, 1 bullish
    htf: float
    structure: float  # bos+choch+ob+fvg average
    liquidity: float
    momentum: float  # heatmap momentum or confidence momentum share
    news: float
    atr: float  # normalized 0-1 volatility proxy
    risk: float  # risk quality / RR band
    confidence: float  # 0-1
    bos: float
    choch: float
    order_block: float
    fvg: float


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _trend_to_score(trend: str | None) -> float:
    value = (trend or "").upper()
    if value in {"BULLISH", "BULL"}:
        return 1.0
    if value in {"BEARISH", "BEAR"}:
        return -1.0
    return 0.0


def extract_similarity_features(
    recommendation: Recommendation | Any,
    *,
    analysis: dict[str, Any] | None = None,
) -> SimilarityFeatures:
    """Extract comparable features from a stored or in-flight recommendation."""
    analysis_data: dict[str, Any] = {}
    if analysis and isinstance(analysis, dict):
        analysis_data = analysis
    else:
        raw = getattr(recommendation, "analysis", None)
        if isinstance(raw, dict):
            analysis_data = raw

    validation = getattr(recommendation, "validation", None) or {}
    if hasattr(validation, "model_dump"):
        validation = validation.model_dump()
    if not isinstance(validation, dict):
        validation = {}

    breakdown = getattr(recommendation, "confidence_breakdown", None) or {}
    if hasattr(breakdown, "model_dump"):
        breakdown = breakdown.model_dump()
    if not isinstance(breakdown, dict):
        breakdown = {}

    heatmap = getattr(recommendation, "market_heatmap", None) or {}
    if hasattr(heatmap, "model_dump"):
        heatmap = heatmap.model_dump()
    if not isinstance(heatmap, dict):
        heatmap = {}

    checklist = getattr(recommendation, "institutional_checklist", None) or []
    if not isinstance(checklist, list):
        checklist = []
    checklist_map = {}
    for item in checklist:
        if hasattr(item, "model_dump"):
            item = item.model_dump()
        if isinstance(item, dict):
            checklist_map[str(item.get("name", "")).lower()] = bool(item.get("passed"))

    trend_raw = getattr(recommendation, "trend", None)
    if hasattr(trend_raw, "value"):
        trend_raw = trend_raw.value
    trend_score = _trend_to_score(str(trend_raw or ""))

    mtf = analysis_data.get("multi_timeframe") or {}
    if not isinstance(mtf, dict):
        mtf = {}
    htf_score = _trend_to_score(
        str(mtf.get("overall_trend") or mtf.get("trend") or ""),
    )

    bos = 1.0 if validation.get("bos") else 0.0
    choch = 1.0 if validation.get("choch") else 0.0
    has_ob = 1.0 if checklist_map.get("order block") else (
        1.0 if (analysis_data.get("smart_money") or {}).get("order_block") else 0.0
    )
    has_fvg = 1.0 if checklist_map.get("fair value gap") else (
        1.0 if (analysis_data.get("smart_money") or {}).get("fvg") else 0.0
    )
    structure = (bos + choch + has_ob + has_fvg) / 4.0

    liquidity = 1.0 if validation.get("liquidity") else 0.0
    if checklist_map.get("liquidity sweep"):
        liquidity = max(liquidity, 1.0)
    if heatmap.get("liquidity") is not None:
        liquidity = max(liquidity, _clamp01(float(heatmap["liquidity"]) / 100.0))

    momentum = _clamp01(float(heatmap.get("momentum", 0) or 0) / 100.0)
    if not momentum and breakdown.get("momentum") is not None:
        max_m = float(breakdown.get("momentum_max") or 15) or 15.0
        momentum = _clamp01(float(breakdown["momentum"]) / max_m)

    news = 1.0 if validation.get("news") else 0.0
    if heatmap.get("news") is not None:
        news = _clamp01(float(heatmap["news"]) / 100.0)

    indicators = analysis_data.get("indicators") or {}
    if not isinstance(indicators, dict):
        indicators = {}
    atr_raw = indicators.get("atr")
    atr = 0.5
    if atr_raw is not None:
        try:
            # Soft normalize: treat relative ATR from heatmap volatility when present.
            atr = _clamp01(float(atr_raw))
            if atr > 1.0:
                atr = _clamp01(atr / (abs(float(getattr(recommendation, "entry_price", 0) or getattr(recommendation, "entry", 0) or 1.0)) + 1e-9) * 50)
        except (TypeError, ValueError):
            atr = 0.5
    if heatmap.get("volatility") is not None:
        atr = _clamp01(float(heatmap["volatility"]) / 100.0)

    rr = float(getattr(recommendation, "risk_reward", 0) or 0)
    risk = _clamp01(rr / 4.0)
    if breakdown.get("risk") is not None:
        max_r = float(breakdown.get("risk_max") or 5) or 5.0
        risk = max(risk, _clamp01(float(breakdown["risk"]) / max_r))

    confidence = _clamp01(float(getattr(recommendation, "confidence", 0) or 0) / 100.0)

    return SimilarityFeatures(
        trend=trend_score,
        htf=htf_score,
        structure=structure,
        liquidity=liquidity,
        momentum=momentum,
        news=news,
        atr=atr,
        risk=risk,
        confidence=confidence,
        bos=bos,
        choch=choch,
        order_block=has_ob,
        fvg=has_fvg,
    )


def similarity_score(a: SimilarityFeatures, b: SimilarityFeatures) -> float:
    """Weighted similarity in [0, 1]."""
    weights = {
        "trend": float(settings.SIMILARITY_WEIGHT_TREND),
        "structure": float(settings.SIMILARITY_WEIGHT_STRUCTURE),
        "liquidity": float(settings.SIMILARITY_WEIGHT_LIQUIDITY),
        "momentum": float(settings.SIMILARITY_WEIGHT_MOMENTUM),
        "news": float(settings.SIMILARITY_WEIGHT_NEWS),
        "atr": float(settings.SIMILARITY_WEIGHT_ATR),
        "risk": float(settings.SIMILARITY_WEIGHT_RISK),
    }
    total_w = sum(weights.values()) or 1.0

    def prox(x: float, y: float, scale: float = 1.0) -> float:
        return max(0.0, 1.0 - abs(x - y) / scale)

    # Trend combines LTF + HTF
    trend_sim = 0.6 * prox(a.trend, b.trend, 2.0) + 0.4 * prox(a.htf, b.htf, 2.0)
    parts = {
        "trend": trend_sim,
        "structure": prox(a.structure, b.structure),
        "liquidity": prox(a.liquidity, b.liquidity),
        "momentum": prox(a.momentum, b.momentum),
        "news": prox(a.news, b.news),
        "atr": prox(a.atr, b.atr),
        "risk": prox(a.risk, b.risk),
    }
    # Confidence band soft match (±10% ≈ 0.1)
    conf_bonus = 0.05 * prox(a.confidence, b.confidence, 0.2)
    score = sum(parts[k] * weights[k] for k in weights) / total_w + conf_bonus
    return _clamp01(score)


class HistoricalSimilarityService:
    """
    Find historically similar labeled recommendations.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.learning_repo = LearningRepository(db)
        self.recommendation_repo = RecommendationRepository(db)

    def find_similar(
        self,
        recommendation: Recommendation | Any,
        *,
        analysis: dict[str, Any] | None = None,
        top_n: int | None = None,
        labeled_only: bool = True,
    ) -> list[tuple[Recommendation, float, RecommendationOutcome | None]]:
        """
        Return top similar (recommendation, score, outcome) tuples.
        """
        top_n = top_n or int(settings.PROBABILITY_SIMILAR_TOP_N)
        symbol = str(getattr(recommendation, "symbol", "") or "").upper()
        timeframe = str(getattr(recommendation, "timeframe", "") or "").upper()
        signal = getattr(recommendation, "signal", None)
        if hasattr(signal, "value"):
            signal = signal.value
        signal_str = str(signal or "").upper()
        exclude_id = getattr(recommendation, "id", None)

        query_features = extract_similarity_features(
            recommendation,
            analysis=analysis,
        )

        results: list[tuple[Recommendation, float, RecommendationOutcome | None]] = []

        if labeled_only:
            candidates = self.learning_repo.list_labeled_recommendations(
                symbol=symbol,
                timeframe=timeframe,
                signal=signal_str or None,
                limit=int(settings.PROBABILITY_CANDIDATE_LIMIT),
                exclude_id=int(exclude_id) if exclude_id is not None else None,
            )
            for rec, outcome in candidates:
                # Confidence band filter (±10)
                if abs(int(rec.confidence) - int(getattr(recommendation, "confidence", 0) or 0)) > 15:
                    # Soft filter: still allow but will score lower via confidence term
                    pass
                feat = extract_similarity_features(rec)
                score = similarity_score(query_features, feat)
                results.append((rec, score, outcome))
        else:
            candidates = self.recommendation_repo.get_candidates_for_similarity(
                symbol=symbol,
                timeframe=timeframe,
                signal=signal_str or None,
                exclude_id=int(exclude_id) if exclude_id is not None else None,
                limit=int(settings.PROBABILITY_CANDIDATE_LIMIT),
            )
            for rec in candidates:
                feat = extract_similarity_features(rec)
                score = similarity_score(query_features, feat)
                results.append((rec, score, None))

        results.sort(key=lambda row: row[1], reverse=True)
        top = results[:top_n]
        logger.debug(
            "Similarity %s %s %s candidates=%d top=%d",
            symbol,
            timeframe,
            signal_str,
            len(results),
            len(top),
        )
        return top

    def to_items(
        self,
        rows: list[tuple[Recommendation, float, RecommendationOutcome | None]],
    ) -> list[SimilarRecommendationItem]:
        items: list[SimilarRecommendationItem] = []
        for rec, score, outcome in rows:
            trend = rec.trend.value if hasattr(rec.trend, "value") else str(rec.trend)
            signal = rec.signal.value if hasattr(rec.signal, "value") else str(rec.signal)
            items.append(
                SimilarRecommendationItem(
                    id=int(rec.id),
                    symbol=rec.symbol,
                    timeframe=rec.timeframe,
                    signal=signal,
                    confidence=int(rec.confidence),
                    trend=trend,
                    risk_reward=float(rec.risk_reward or 0),
                    similarity=round(score, 4),
                    outcome_label=outcome.label if outcome else None,
                    pnl_proxy=float(outcome.pnl_proxy) if outcome else None,
                    trade_probability=getattr(rec, "trade_probability", None),
                    trade_quality=getattr(rec, "trade_quality", None),
                    quality_grade=getattr(rec, "quality_grade", None) or None,
                    created_at=rec.created_at.isoformat() if rec.created_at else None,
                )
            )
        return items
