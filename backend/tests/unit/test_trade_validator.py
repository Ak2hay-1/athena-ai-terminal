from app.ai.models import AIRecommendation
from app.analysis.trade_validator import trade_validator


def test_trade_validator_blocks_hold():
    recommendation = AIRecommendation(
        signal="HOLD",
        confidence=90,
        risk_reward=3,
        confluence=80,
    )
    decision = trade_validator.validate(recommendation)
    assert decision.execute is False


def test_trade_validator_blocks_no_trade():
    recommendation = AIRecommendation(
        signal="NO_TRADE",
        confidence=90,
        risk_reward=3,
        confluence=80,
    )
    decision = trade_validator.validate(recommendation)
    assert decision.execute is False


def test_trade_validator_blocks_high_impact_news():
    recommendation = AIRecommendation(
        signal="BUY",
        confidence=90,
        risk_reward=3,
        confluence=80,
        entry=1.10000,
        stop_loss=1.09800,
        take_profit=1.10400,
    )
    decision = trade_validator.validate(
        recommendation,
        news_context={"high_impact_upcoming": True},
    )
    assert decision.execute is False


def test_trade_validator_blocks_collapsed_levels():
    recommendation = AIRecommendation(
        signal="BUY",
        confidence=90,
        risk_reward=2,
        confluence=80,
        entry=1.27,
        stop_loss=1.27,
        take_profit=1.27,
    )
    decision = trade_validator.validate(recommendation)
    assert decision.execute is False
    assert any("Collapsed" in reason for reason in decision.reasons)
