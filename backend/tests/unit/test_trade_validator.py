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


def test_trade_validator_blocks_high_impact_news():
    recommendation = AIRecommendation(
        signal="BUY",
        confidence=90,
        risk_reward=3,
        confluence=80,
    )
    decision = trade_validator.validate(
        recommendation,
        news_context={"high_impact_upcoming": True},
    )
    assert decision.execute is False
