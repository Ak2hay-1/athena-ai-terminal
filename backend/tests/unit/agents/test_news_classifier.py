"""Unit tests for news classification and impact mapping."""

from __future__ import annotations

from app.agents.news.classifier import classify_headline
from app.agents.news.impact import enrich_impact
from app.agents.news.impact import normalize_impact


def test_classify_bullish_bearish_neutral() -> None:
    bull = classify_headline("Gold rally continues with strong bullish breakout")
    bear = classify_headline("Market crash risk as inflation and rate hike fears rise")
    neutral = classify_headline("Markets closed for holiday")
    assert bull["sentiment"] == "Bullish"
    assert bear["sentiment"] == "Bearish"
    assert neutral["sentiment"] == "Neutral"


def test_impact_and_symbol_mapping() -> None:
    items = enrich_impact(
        [
            {
                "title": "ECB comments on EURUSD outlook",
                "symbols": ["EURUSD"],
                "impact": "HIGH",
            }
        ]
    )
    assert items[0]["impact"] == "High"
    assert "EUR" in items[0]["currencies"] or "USD" in items[0]["currencies"]
    assert "EURUSD" in items[0]["symbols"]
    assert normalize_impact("medium") == "Medium"
