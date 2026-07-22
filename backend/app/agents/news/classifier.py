"""
News sentiment classification — Bullish / Bearish / Neutral.
"""

from __future__ import annotations

from typing import Any

from app.analysis.news_sentiment import news_sentiment_engine


def classify_headline(title: str, summary: str | None = None) -> dict[str, Any]:
    text_parts = [title]
    if summary:
        text_parts.append(summary)
    result = news_sentiment_engine.analyze(text_parts)
    label = result.sentiment
    if label not in {"BULLISH", "BEARISH", "NEUTRAL"}:
        label = "NEUTRAL"
    # Normalize to title case labels from plan
    display = {"BULLISH": "Bullish", "BEARISH": "Bearish", "NEUTRAL": "Neutral"}[label]
    return {
        "sentiment": display,
        "sentiment_code": label,
        "score": result.score,
        "confidence": result.confidence,
        "reasons": result.reasons,
    }


def classify_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified: list[dict[str, Any]] = []
    for item in items:
        sentiment = classify_headline(item.get("title") or "", item.get("summary"))
        enriched = dict(item)
        enriched.update(sentiment)
        classified.append(enriched)
    return classified
