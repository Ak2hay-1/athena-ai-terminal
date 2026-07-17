"""Unit tests for GeminiProvider (SDK fully mocked)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.schemas.context import ChatMessage
from app.ai.schemas.context import MarketContext
from app.ai.schemas.context import NewsItem
from app.ai.schemas.context import TradeCandidate


@pytest.fixture
def gemini(monkeypatch) -> GeminiProvider:
    monkeypatch.setattr(
        "app.ai.providers.gemini_provider.settings",
        SimpleNamespace(
            GEMINI_API_KEY="test-key",
            GEMINI_MODEL="gemini-test-model",
            GEMINI_EMBED_MODEL="embed-test-model",
            AI_TIMEOUT=30,
            AI_MAX_RETRIES=3,
        ),
    )
    provider = GeminiProvider()
    provider._client = object()  # bypass real client init
    return provider


def _context() -> MarketContext:
    return MarketContext(
        symbol="XAUUSD",
        timeframe="M5",
        trend="BULLISH",
        market_structure={"bos_active": True},
        liquidity={"buy_liquidity": True},
        order_blocks={"active": True},
        fvg={"active": False},
        volume={"latest": 1200},
        volatility={"atr": 1.2},
        news_summary="USD soft",
        trade_candidate=TradeCandidate(
            signal="BUY",
            confidence=88,
            entry=2350.0,
            stop_loss=2340.0,
            take_profit=2370.0,
        ),
    )


def test_model_comes_from_settings(gemini: GeminiProvider):
    assert gemini.model_name() == "gemini-test-model"
    assert gemini.embed_model == "embed-test-model"


def test_structured_context_excludes_ohlc(gemini: GeminiProvider):
    payload = gemini._structured_context(_context())
    assert "candles" not in payload
    assert "ohlc" not in payload
    assert payload["trend"] == "BULLISH"
    assert payload["fvgs"] == {"active": False}
    assert payload["confidence"] == 88
    assert "trade_candidate" in payload


def test_generate_trade_explanation_validates_json(gemini: GeminiProvider, monkeypatch):
    monkeypatch.setattr(
        gemini,
        "generate_text",
        lambda **kwargs: SimpleNamespace(
            text='{"reason":["Structure supports long","Liquidity above"]}',
            model="gemini-test-model",
            provider="gemini",
            latency_ms=10,
            prompt_tokens=11,
            completion_tokens=22,
        ),
    )
    result = gemini.generate_trade_explanation(_context())
    assert result.success is True
    assert result.reasons == ["Structure supports long", "Liquidity above"]
    assert result.provider == "gemini"
    assert result.model == "gemini-test-model"


def test_generate_market_summary(gemini: GeminiProvider, monkeypatch):
    monkeypatch.setattr(
        gemini,
        "generate_text",
        lambda **kwargs: SimpleNamespace(
            text='{"summary":"Bullish bias","bullets":["BOS"],"bias":"BULLISH"}',
            model="gemini-test-model",
            provider="gemini",
            latency_ms=5,
            prompt_tokens=1,
            completion_tokens=2,
        ),
    )
    result = gemini.generate_market_summary(_context())
    assert result.summary == "Bullish bias"
    assert result.bias == "BULLISH"
    assert result.bullets == ["BOS"]


def test_summarize_news(gemini: GeminiProvider, monkeypatch):
    monkeypatch.setattr(
        gemini,
        "generate_text",
        lambda **kwargs: SimpleNamespace(
            text='{"summary":"Risk-on","bullets":["NFP"],"overall_sentiment":"BULLISH"}',
            model="gemini-test-model",
            provider="gemini",
            latency_ms=5,
            prompt_tokens=1,
            completion_tokens=2,
        ),
    )
    result = gemini.summarize_news(
        [NewsItem(title="NFP beats", summary="Strong jobs")],
        context=_context(),
    )
    assert result.overall_sentiment == "BULLISH"
    assert "Risk-on" in result.summary


def test_generate_chat_response_trims_history(gemini: GeminiProvider, monkeypatch):
    seen: dict = {}

    def fake_chat(*, messages, system=None):
        seen["count"] = len(messages)
        seen["system"] = system
        return SimpleNamespace(
            text="Athena reply",
            model="gemini-test-model",
            provider="gemini",
            latency_ms=3,
            prompt_tokens=1,
            completion_tokens=1,
        )

    monkeypatch.setattr(gemini, "chat", fake_chat)
    messages = [
        ChatMessage(role="user", content=f"msg-{index}")
        for index in range(12)
    ]
    result = gemini.generate_chat_response(messages, context=_context())
    assert result.reply == "Athena reply"
    assert seen["count"] == 8
    assert seen["system"]


def test_backoff_retries_on_429(gemini: GeminiProvider, monkeypatch):
    gemini.max_retries = 3
    calls = {"n": 0}
    sleeps: list[float] = []

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            exc = RuntimeError("429 RESOURCE_EXHAUSTED")
            exc.code = 429  # type: ignore[attr-defined]
            raise exc
        return "ok"

    monkeypatch.setattr(
        "app.ai.providers.gemini_provider.time.sleep",
        lambda delay: sleeps.append(delay),
    )
    assert gemini._with_backoff(flaky, label="test") == "ok"
    assert calls["n"] == 3
    assert len(sleeps) == 2


def test_health_false_without_key(monkeypatch):
    monkeypatch.setattr(
        "app.ai.providers.gemini_provider.settings",
        SimpleNamespace(
            GEMINI_API_KEY="",
            GEMINI_MODEL="gemini-test-model",
            GEMINI_EMBED_MODEL="embed-test-model",
            AI_TIMEOUT=30,
            AI_MAX_RETRIES=3,
        ),
    )
    assert GeminiProvider().health() is False
