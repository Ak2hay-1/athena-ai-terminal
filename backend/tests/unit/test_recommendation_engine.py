"""Tests for recommendation engine with institutional risk plan."""

from __future__ import annotations

import pandas as pd

from app.ai.recommendation_engine import RecommendationEngine
from app.ai.schemas.responses import TradeExplanationResponse
from app.core.enums import RecommendationSignal
from app.risk.models import EntryType
from app.risk.models import TradePlan
from app.risk.models import ValidationFlags


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

    monkeypatch.setattr(
        "app.ai.recommendation_engine.market_analyzer.analyze",
        lambda *args, **kwargs: {
            "indicators": {"atr": 0.05},
            "trend": {"direction": "BULLISH"},
            "confluence": {"score": 72},
        },
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.risk_engine.build_plan",
        lambda *args, **kwargs: TradePlan(
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
        ),
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

    monkeypatch.setattr(
        "app.ai.recommendation_engine.market_analyzer.analyze",
        lambda *args, **kwargs: {
            "trend": {"direction": "SIDEWAYS"},
            "confluence": {"score": 20},
        },
    )
    monkeypatch.setattr(
        "app.ai.recommendation_engine.risk_engine.build_plan",
        lambda *args, **kwargs: TradePlan(
            signal="NO_TRADE",
            confidence=35,
            trend="SIDEWAYS",
            reasons=["Market trend is sideways; no trade."],
            validation=ValidationFlags(trend=False),
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
