"""Tests for recommendation engine with institutional risk plan."""

from __future__ import annotations

import pandas as pd

from app.ai.recommendation_engine import RecommendationEngine
from app.ai.schemas.responses import TradeExplanationResponse
from app.core.enums import RecommendationSignal
from app.risk.models import EntryType
from app.risk.models import RiskPlanBundle
from app.risk.models import StructureContext
from app.risk.models import TradePlan
from app.risk.models import ValidationFlags
from app.risk.models import ZoneLevel


def _ctx(**overrides) -> StructureContext:
    base = dict(
        symbol="EURUSD",
        timeframe="M15",
        price=1.2000,
        atr=0.0020,
        trend="BULLISH",
        volume=200,
        avg_volume=100,
        bos_active=True,
        bos_direction="bullish",
        choch_active=True,
        choch_direction="bullish",
        in_premium=False,
        in_discount=True,
        equilibrium=1.195,
        range_high=1.210,
        range_low=1.180,
        bullish_order_blocks=[
            ZoneLevel(price=1.198, kind="order_block", high=1.199, low=1.197),
        ],
        bullish_fvgs=[
            ZoneLevel(price=1.1975, kind="fvg", high=1.1985, low=1.1965),
        ],
        liquidity_sweep_lows=[1.185],
        liquidity_targets_high=[ZoneLevel(price=1.210, kind="equal_high")],
        multi_tf_trend="BULLISH",
        news_high_impact=False,
        news_sentiment=0.3,
        atr_ok=True,
        tight_range=False,
    )
    base.update(overrides)
    return StructureContext(**base)


def test_levels_come_from_risk_engine_not_ai(monkeypatch):
    engine = RecommendationEngine()
    dataframe = pd.DataFrame(
        {
            "open": [1.0, 1.1],
            "high": [1.2, 1.3],
            "low": [0.9, 1.0],
            "close": [1.1, 1.2],
            "tick_volume": [100, 120],
        }
    )

    plan = TradePlan(
        signal="BUY",
        entry=1.20000,
        entry_type=EntryType.LIMIT,
        stop_loss=1.19500,
        take_profit=1.21000,
        risk_pips=50,
        reward_pips=100,
        risk_reward=2.0,
        confidence=84,
        sl_reason="Below latest swing low with ATR buffer",
        tp_reason="Previous liquidity high",
        entry_reason="Limit entry at bullish order block",
        trend="BULLISH",
        validation=ValidationFlags(
            trend=True,
            bos=True,
            volume=True,
            atr=True,
            liquidity=True,
            news=True,
            structure_sl=True,
            risk_distance=True,
            risk_reward=True,
        ),
    )

    monkeypatch.setattr(
        "app.ai.recommendation_engine.settings.QUALIFICATION_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.settings.PORTFOLIO_AWARENESS_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.settings.MIN_SETUP_QUALITY",
        0,
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.settings.MIN_CONFIDENCE",
        0,
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.market_analyzer.analyze",
        lambda *args, **kwargs: {
            "indicators": {
                "atr": 0.05,
                "rsi": 58,
                "macd": {"value": 0.1, "signal": 0.05, "bullish": True},
            },
            "trend": {"direction": "BULLISH"},
            "confluence": {"score": 72},
        },
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.risk_engine.build_plan",
        lambda *args, **kwargs: RiskPlanBundle(plan=plan, context=_ctx()),
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.ai_service.generate_trade_explanation",
        lambda context: TradeExplanationResponse(
            reasons=["AI narrative only"],
            success=True,
            provider="test",
            model="mock",
        ),
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.setup_quality_service.score",
        lambda **kwargs: type(
            "Q",
            (),
            {
                "score": 90,
                "grade": "Elite",
                "components": {},
                "category": "elite",
            },
        )(),
    )

    result = engine.analyze(
        dataframe,
        symbol="EURUSD",
        timeframe="M15",
    )

    assert result.signal == RecommendationSignal.BUY
    assert result.confidence == 84
    assert result.entry == 1.20000
    assert result.stop_loss == 1.19500
    assert result.take_profit == 1.21000
    assert result.entry_type == "LIMIT"
    assert "AI narrative only" in result.reason
    assert result.sl_reason.startswith("Below")
    assert result.confidence_breakdown is not None
    total = (
        result.confidence_breakdown.trend
        + result.confidence_breakdown.momentum
        + result.confidence_breakdown.structure
        + result.confidence_breakdown.liquidity
        + result.confidence_breakdown.news
        + result.confidence_breakdown.risk
    )
    assert total == 84
    assert len(result.institutional_checklist) == 9
    assert result.market_heatmap is not None
    assert 0 <= result.market_heatmap.trend <= 100
    assert result.entry_zone is not None
    assert result.entry_zone.aggressive > 0


def test_no_trade_plan_is_returned(monkeypatch):
    engine = RecommendationEngine()
    dataframe = pd.DataFrame(
        {
            "open": [1.0, 1.1],
            "high": [1.2, 1.3],
            "low": [0.9, 1.0],
            "close": [1.1, 1.2],
            "tick_volume": [100, 120],
        }
    )

    plan = TradePlan(
        signal="NO_TRADE",
        confidence=35,
        trend="SIDEWAYS",
        reasons=["Market trend is sideways; no trade."],
        validation=ValidationFlags(trend=False),
    )

    monkeypatch.setattr(
        "app.ai.recommendation_engine.settings.QUALIFICATION_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.settings.PORTFOLIO_AWARENESS_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.market_analyzer.analyze",
        lambda *args, **kwargs: {
            "trend": {"direction": "SIDEWAYS"},
            "confluence": {"score": 20},
        },
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.risk_engine.build_plan",
        lambda *args, **kwargs: RiskPlanBundle(
            plan=plan,
            context=_ctx(trend="SIDEWAYS", multi_tf_trend="SIDEWAYS"),
        ),
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.ai_service.generate_trade_explanation",
        lambda context: TradeExplanationResponse(
            reasons=["No clear structure"],
            success=True,
        ),
    )

    result = engine.analyze(dataframe, symbol="GBPUSD", timeframe="M5")
    assert result.signal == RecommendationSignal.NO_TRADE
    assert result.confidence == 35
    assert result.confidence_breakdown is not None
    assert result.market_heatmap is not None
