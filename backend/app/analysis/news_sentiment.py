"""
Athena News Sentiment Engine.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class NewsSentiment:

    score: int

    sentiment: str

    confidence: float

    reasons: list[str]


class NewsSentimentEngine:
    """
    News sentiment evaluator.

    Current version accepts already-fetched news.

    Later:
        News API
        RSS
        Economic Calendar
        AI News Summaries
    """

    POSITIVE = {

        "bullish",

        "growth",

        "buy",

        "breakout",

        "strong",

        "positive",

        "rate cut",

        "gold rally",

    }

    NEGATIVE = {

        "bearish",

        "sell",

        "crash",

        "recession",

        "negative",

        "war",

        "inflation",

        "rate hike",

    }

    def analyze(
        self,
        headlines: list[str],
    ) -> NewsSentiment:

        score = 0

        reasons: list[str] = []

        for headline in headlines:

            text = headline.lower()

            for word in self.POSITIVE:

                if word in text:

                    score += 1

                    reasons.append(
                        f"Positive: {word}"
                    )

            for word in self.NEGATIVE:

                if word in text:

                    score -= 1

                    reasons.append(
                        f"Negative: {word}"
                    )

        sentiment = "NEUTRAL"

        if score > 0:

            sentiment = "BULLISH"

        elif score < 0:

            sentiment = "BEARISH"

        confidence = min(
            abs(score) * 10,
            100,
        )

        return NewsSentiment(

            score=score,

            sentiment=sentiment,

            confidence=confidence,

            reasons=reasons,

        )


news_sentiment_engine = NewsSentimentEngine()