from app.analysis.news_sentiment import news_sentiment_engine


def test_news_sentiment_bullish():
    result = news_sentiment_engine.analyze(
        ["Gold rally after rate cut and bullish growth"]
    )
    assert result.sentiment == "BULLISH"
    assert result.score > 0


def test_news_sentiment_bearish():
    result = news_sentiment_engine.analyze(
        ["Bearish crash fears as war and recession deepen"]
    )
    assert result.sentiment == "BEARISH"
    assert result.score < 0
