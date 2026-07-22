"""Unit tests for deterministic trade probability stack."""

from __future__ import annotations

from types import SimpleNamespace

from app.learning.signal_model import FEATURE_ORDER
from app.learning.signal_model import feature_vector_from_recommendation
from app.schemas.probability import TradeProbabilityResult
from app.services.historical_insights_service import HistoricalInsightsService
from app.services.historical_similarity_service import SimilarityFeatures
from app.services.historical_similarity_service import extract_similarity_features
from app.services.historical_similarity_service import similarity_score
from app.services.trade_probability_service import classify_confidence_category
from app.services.trade_probability_service import format_hold_time
from app.services.trade_quality_service import TradeQualityService
from app.services.trade_quality_service import classify_quality_grade
from app.services.trade_comparison_service import TradeComparisonService
from app.models.recommendation import Recommendation
from app.core.enums import RecommendationSignal
from app.core.enums import TrendDirection


def test_feature_vector_order_and_no_label_leakage():
    vector = feature_vector_from_recommendation(
        analysis={
            "confluence": {"score": 80},
            "indicators": {
                "rsi": 60,
                "macd": {"bullish": True},
            },
            "news": {"score": 0.4},
            "multi_timeframe": {"overall_trend": "BULLISH"},
        },
        confluence=80,
    )
    assert len(vector) == len(FEATURE_ORDER)
    assert vector[0] == 0.8
    assert 0.0 <= vector[1] <= 1.0
    assert vector[2] == 1.0
    assert vector[4] == 1.0


def test_similarity_weights_prefer_aligned_structure():
    a = SimilarityFeatures(
        trend=1.0,
        htf=1.0,
        structure=1.0,
        liquidity=1.0,
        momentum=0.8,
        news=0.8,
        atr=0.5,
        risk=0.7,
        confidence=0.86,
        bos=1.0,
        choch=1.0,
        order_block=1.0,
        fvg=1.0,
    )
    b = SimilarityFeatures(
        trend=1.0,
        htf=1.0,
        structure=0.9,
        liquidity=1.0,
        momentum=0.75,
        news=0.7,
        atr=0.55,
        risk=0.65,
        confidence=0.84,
        bos=1.0,
        choch=1.0,
        order_block=1.0,
        fvg=0.0,
    )
    c = SimilarityFeatures(
        trend=-1.0,
        htf=-1.0,
        structure=0.0,
        liquidity=0.0,
        momentum=0.1,
        news=0.0,
        atr=0.9,
        risk=0.1,
        confidence=0.3,
        bos=0.0,
        choch=0.0,
        order_block=0.0,
        fvg=0.0,
    )
    assert similarity_score(a, b) > similarity_score(a, c)


def test_extract_features_from_recommendation_like_object():
    rec = SimpleNamespace(
        trend="BULLISH",
        confidence=80,
        risk_reward=2.5,
        entry_price=1.1,
        validation={"bos": True, "choch": True, "liquidity": True, "news": True},
        confidence_breakdown={"momentum": 12, "momentum_max": 15, "risk": 4, "risk_max": 5},
        market_heatmap={"momentum": 70, "liquidity": 65, "volatility": 40, "news": 55},
        institutional_checklist=[
            {"name": "Order Block", "passed": True},
            {"name": "Fair Value Gap", "passed": False},
        ],
        analysis={},
    )
    features = extract_similarity_features(rec)
    assert features.trend == 1.0
    assert features.bos == 1.0
    assert features.order_block == 1.0
    assert features.fvg == 0.0


def test_confidence_category_and_low_sample():
    assert classify_confidence_category(96, low_sample=False) == "Exceptional"
    assert classify_confidence_category(88, low_sample=False) == "Very High"
    assert classify_confidence_category(78, low_sample=False) == "High"
    assert classify_confidence_category(65, low_sample=False) == "Moderate"
    assert classify_confidence_category(45, low_sample=False) == "Low"
    assert classify_confidence_category(20, low_sample=False) == "Very Low"
    assert classify_confidence_category(90, low_sample=True) == "LOW_SAMPLE"


def test_format_hold_time_m15():
    text = format_hold_time("M15")
    assert "Hours" in text or "Minutes" in text


def test_quality_grades():
    assert classify_quality_grade(96) == "Institutional"
    assert classify_quality_grade(91) == "A+"
    assert classify_quality_grade(86) == "A"
    assert classify_quality_grade(82) == "B+"
    assert classify_quality_grade(72) == "B"
    assert classify_quality_grade(62) == "C"
    assert classify_quality_grade(40) == "D"


def test_trade_quality_service_bounds():
    service = TradeQualityService()
    rec = SimpleNamespace(
        confidence=86,
        risk_reward=2.8,
        confidence_breakdown={
            "trend": 30,
            "trend_max": 35,
            "structure": 18,
            "structure_max": 20,
            "momentum": 12,
            "momentum_max": 15,
            "liquidity": 10,
            "liquidity_max": 15,
            "risk": 4,
            "risk_max": 5,
        },
        market_heatmap={
            "trend": 90,
            "structure": 80,
            "momentum": 70,
            "liquidity": 65,
            "risk": 85,
        },
    )
    prob = TradeProbabilityResult(
        probability=76,
        historical_win_rate=74,
        similar_trades=50,
        confidence_category="High",
    )
    result = service.score(rec, prob)
    assert 0 <= result.trade_quality <= 100
    assert result.grade


def test_insights_insufficient_sample():
    service = HistoricalInsightsService()
    insights = service.build([])
    assert insights
    assert "Insufficient" in insights[0]


def test_comparison_winner_by_quality():
    # Build minimal ORM-like objects without DB
    a = Recommendation(
        symbol="EURUSD",
        timeframe="M15",
        signal=RecommendationSignal.BUY,
        confidence=86,
        trend=TrendDirection.BULLISH,
        confluence=70,
        entry_price=1.1,
        stop_loss=1.09,
        take_profit=1.12,
        risk_reward=3.0,
        validation={"bos": True, "choch": True, "liquidity": True, "news": True, "structure_sl": True},
        trade_probability=77,
        trade_quality=91,
        quality_grade="A+",
        probability_detail={"probability": 77, "similar_trades": 40},
    )
    b = Recommendation(
        symbol="EURUSD",
        timeframe="M15",
        signal=RecommendationSignal.BUY,
        confidence=74,
        trend=TrendDirection.BULLISH,
        confluence=60,
        entry_price=1.1,
        stop_loss=1.09,
        take_profit=1.115,
        risk_reward=2.2,
        validation={"bos": True, "news": False},
        trade_probability=69,
        trade_quality=78,
        quality_grade="B",
        probability_detail={"probability": 69, "similar_trades": 40},
    )
    # Bypass DB by calling compare directly with a stub service
    service = object.__new__(TradeComparisonService)
    service.probability_service = SimpleNamespace(
        estimate=lambda rec: TradeProbabilityResult.model_validate(
            rec.probability_detail or {},
        )
    )
    service.quality_service = TradeQualityService()
    result = TradeComparisonService.compare(service, a, b)
    assert result.winner == "A"
    assert result.comparison["confidence"].winner == "A"
    assert result.comparison["rr"].winner == "A"
