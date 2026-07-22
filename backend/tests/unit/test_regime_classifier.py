"""Regime classifier unit tests."""

from app.learning.regime_classifier import classify_regime


def test_news_driven():
    assert classify_regime(news_blocked=True) == "NEWS_DRIVEN"
    assert classify_regime(news_score=0.9) == "NEWS_DRIVEN"


def test_volatility_regimes():
    assert (
        classify_regime(atr=3.0, atr_baseline=1.0, trend="BULLISH")
        == "HIGH_VOLATILITY"
    )
    assert (
        classify_regime(atr=0.4, atr_baseline=1.0, trend="BULLISH")
        == "LOW_VOLATILITY"
    )


def test_structure_regimes():
    assert classify_regime(choch_active=True, trend="BULLISH") == "REVERSAL"
    assert classify_regime(bos_active=True, trend="BULLISH") == "BREAKOUT"
    assert classify_regime(trend="BULLISH") == "TRENDING"
    assert classify_regime(trend="SIDEWAYS") == "RANGING"
