"""Unit tests for AzureProvider (SDK fully mocked)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.ai.providers.azure_provider import AzureProvider
from app.ai.providers.factory import configured_model_name
from app.ai.providers.factory import resolve_provider
from app.ai.schemas.context import ChatMessage
from app.ai.schemas.context import MarketContext
from app.ai.schemas.context import NewsItem
from app.ai.schemas.context import TradeCandidate


@pytest.fixture
def azure(monkeypatch) -> AzureProvider:
    monkeypatch.setattr(
        "app.ai.providers.azure_provider.settings",
        SimpleNamespace(
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com/",
            AZURE_OPENAI_API_KEY="test-key",
            AZURE_OPENAI_DEPLOYMENT="gpt-5-mini",
            AZURE_OPENAI_API_VERSION="2024-12-01-preview",
            AZURE_OPENAI_EMBED_DEPLOYMENT="text-embedding-3-small",
            AI_TIMEOUT=30,
            AI_MAX_RETRIES=3,
        ),
    )
    provider = AzureProvider()
    provider._client = MagicMock()
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


def test_model_comes_from_deployment(azure: AzureProvider):
    assert azure.model_name() == "gpt-5-mini"
    assert azure.name == "azure"


def test_structured_context_excludes_ohlc(azure: AzureProvider):
    payload = azure._structured_context(_context())
    assert "candles" not in payload
    assert "ohlc" not in payload
    assert payload["trend"] == "BULLISH"
    assert payload["fair_value_gaps"] == {"active": False}
    assert payload["confidence"] == 88
    assert "trade_candidate" in payload


def test_generate_trade_explanation_validates_json(azure: AzureProvider, monkeypatch):
    monkeypatch.setattr(
        azure,
        "generate_text",
        lambda **kwargs: SimpleNamespace(
            text='{"reason":["Structure supports long","Liquidity above"]}',
            model="gpt-5-mini",
            provider="azure",
            latency_ms=10,
            prompt_tokens=11,
            completion_tokens=22,
        ),
    )
    result = azure.generate_trade_explanation(_context())
    assert result.success is True
    assert result.reasons == ["Structure supports long", "Liquidity above"]
    assert result.provider == "azure"
    assert result.model == "gpt-5-mini"


def test_generate_market_summary(azure: AzureProvider, monkeypatch):
    monkeypatch.setattr(
        azure,
        "generate_text",
        lambda **kwargs: SimpleNamespace(
            text='{"summary":"Bullish bias","bullets":["BOS"],"bias":"BULLISH"}',
            model="gpt-5-mini",
            provider="azure",
            latency_ms=5,
            prompt_tokens=1,
            completion_tokens=2,
        ),
    )
    result = azure.generate_market_summary(_context())
    assert result.summary == "Bullish bias"
    assert result.bias == "BULLISH"
    assert result.bullets == ["BOS"]


def test_summarize_news(azure: AzureProvider, monkeypatch):
    monkeypatch.setattr(
        azure,
        "generate_text",
        lambda **kwargs: SimpleNamespace(
            text='{"summary":"Risk-on","bullets":["NFP"],"overall_sentiment":"BULLISH"}',
            model="gpt-5-mini",
            provider="azure",
            latency_ms=5,
            prompt_tokens=1,
            completion_tokens=2,
        ),
    )
    result = azure.summarize_news(
        [NewsItem(title="NFP beats", summary="Strong jobs")],
        context=_context(),
    )
    assert result.overall_sentiment == "BULLISH"
    assert "Risk-on" in result.summary


def test_generate_chat_response_trims_history(azure: AzureProvider, monkeypatch):
    seen: dict = {}

    def fake_chat(*, messages, system=None):
        seen["count"] = len(messages)
        seen["system"] = system
        return SimpleNamespace(
            text="Athena reply",
            model="gpt-5-mini",
            provider="azure",
            latency_ms=3,
            prompt_tokens=1,
            completion_tokens=1,
        )

    monkeypatch.setattr(azure, "chat", fake_chat)
    messages = [
        ChatMessage(role="user", content=f"msg-{index}")
        for index in range(12)
    ]
    result = azure.generate_chat_response(messages, context=_context())
    assert result.reply == "Athena reply"
    assert seen["count"] == 8
    assert seen["system"]


def test_generate_text_uses_deployment(azure: AzureProvider):
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=20)
    message = SimpleNamespace(content='{"ok":true}')
    choice = SimpleNamespace(message=message)
    response = SimpleNamespace(choices=[choice], usage=usage)
    azure._client.chat.completions.create.return_value = response

    result = azure.generate_text(system="sys", user="usr", json_mode=True)
    assert result.text == '{"ok":true}'
    assert result.provider == "azure"
    assert result.model == "gpt-5-mini"
    assert result.prompt_tokens == 10
    kwargs = azure._client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-5-mini"
    assert kwargs["response_format"] == {"type": "json_object"}


def test_backoff_retries_on_429(azure: AzureProvider, monkeypatch):
    azure.max_retries = 3
    calls = {"n": 0}
    sleeps: list[float] = []

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            exc = RuntimeError("429 rate limit exceeded")
            exc.status_code = 429  # type: ignore[attr-defined]
            raise exc
        return "ok"

    monkeypatch.setattr(
        "app.ai.providers.azure_provider.time.sleep",
        lambda delay: sleeps.append(delay),
    )
    assert azure._with_backoff(flaky, label="test") == "ok"
    assert calls["n"] == 3
    assert len(sleeps) == 2


def test_health_false_without_credentials(monkeypatch):
    monkeypatch.setattr(
        "app.ai.providers.azure_provider.settings",
        SimpleNamespace(
            AZURE_OPENAI_ENDPOINT="",
            AZURE_OPENAI_API_KEY="",
            AZURE_OPENAI_DEPLOYMENT="gpt-5-mini",
            AZURE_OPENAI_API_VERSION="2024-12-01-preview",
            AZURE_OPENAI_EMBED_DEPLOYMENT="",
            AI_TIMEOUT=30,
            AI_MAX_RETRIES=3,
        ),
    )
    assert AzureProvider().health() is False


def test_factory_resolves_azure(monkeypatch):
    monkeypatch.setattr(
        "app.ai.providers.azure_provider.settings",
        SimpleNamespace(
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com/",
            AZURE_OPENAI_API_KEY="test-key",
            AZURE_OPENAI_DEPLOYMENT="gpt-5-mini",
            AZURE_OPENAI_API_VERSION="2024-12-01-preview",
            AZURE_OPENAI_EMBED_DEPLOYMENT="",
            AI_TIMEOUT=30,
            AI_MAX_RETRIES=3,
        ),
    )
    provider = resolve_provider("azure")
    assert isinstance(provider, AzureProvider)
    assert provider.name == "azure"


def test_configured_model_name_azure(monkeypatch):
    monkeypatch.setattr(
        "app.ai.providers.factory.settings",
        SimpleNamespace(
            AI_PROVIDER="azure",
            AZURE_OPENAI_DEPLOYMENT="my-gpt5-mini-deploy",
            GEMINI_MODEL="gemini-2.5-flash",
            CLAUDE_MODEL="claude-sonnet-4-20250514",
            OLLAMA_MODEL="llama3.2",
            OPENAI_MODEL="gpt-4o-mini",
        ),
    )
    assert configured_model_name("azure") == "my-gpt5-mini-deploy"
