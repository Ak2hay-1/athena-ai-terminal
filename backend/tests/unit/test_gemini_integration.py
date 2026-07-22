"""
Integration-style tests for Gemini through AIService.

No live Gemini network calls — SDK / provider methods are mocked.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import importlib

import pytest

from app.ai.schemas.context import ChatMessage
from app.ai.schemas.context import MarketContext
from app.ai.schemas.context import NewsItem
from app.ai.schemas.context import TradeCandidate
from app.ai.schemas.responses import ChatResponse
from app.ai.schemas.responses import MarketSummary
from app.ai.schemas.responses import NewsSummary
from app.ai.schemas.responses import TradeExplanation
from app.ai.services.ai_service import AIService


ai_service_module = importlib.import_module("app.ai.services.ai_service")


class _MemoryCache:
    def __init__(self) -> None:
        self.store: dict[str, dict] = {}

    def get(self, task, state, model):
        key = f"{task}:{state.get('symbol')}:{state.get('confidence')}"
        raw = self.store.get(key)
        return model.model_validate(raw) if raw else None

    def set(self, task, state, value):
        key = f"{task}:{state.get('symbol')}:{state.get('confidence')}"
        self.store[key] = value.model_dump()


class _GeminiMock:
    name = "gemini"

    def __init__(self) -> None:
        self.trade_calls = 0

    def model_name(self) -> str:
        return "gemini-test-model"

    def health(self) -> bool:
        return True

    def generate_trade_explanation(self, context):
        self.trade_calls += 1
        return TradeExplanation(
            reasons=["Gemini narrative"],
            provider="gemini",
            model="gemini-test-model",
            success=True,
        )

    def generate_market_summary(self, context):
        return MarketSummary(
            summary="Market firm",
            bullets=["Trend up"],
            bias="BULLISH",
            provider="gemini",
            model="gemini-test-model",
            success=True,
        )

    def summarize_news(self, items, context=None):
        return NewsSummary(
            summary="News constructive",
            bullets=[items[0].title],
            overall_sentiment="BULLISH",
            provider="gemini",
            model="gemini-test-model",
            success=True,
        )

    def generate_chat_response(self, messages, context=None):
        return ChatResponse(
            reply=f"Echo: {messages[-1].content}",
            provider="gemini",
            model="gemini-test-model",
            success=True,
        )


def _context() -> MarketContext:
    return MarketContext(
        symbol="XAUUSD",
        timeframe="1H",
        trend="Bullish",
        trade_candidate=TradeCandidate(signal="BUY", confidence=88),
    )


@pytest.fixture
def service(monkeypatch) -> AIService:
    cache = _MemoryCache()
    provider = _GeminiMock()
    monkeypatch.setattr(ai_service_module, "response_cache", cache)
    monkeypatch.setattr(ai_service_module, "get_primary_provider", lambda: provider)
    monkeypatch.setattr(ai_service_module, "get_fallback_provider", lambda _p=None: None)
    svc = AIService()
    svc._provider = provider  # type: ignore[attr-defined]
    svc._cache = cache  # type: ignore[attr-defined]
    return svc


def test_ai_service_uses_gemini_high_level_and_caches(service: AIService):
    provider = service._provider  # type: ignore[attr-defined]
    first = service.generate_trade_explanation(_context())
    second = service.generate_trade_explanation(_context())
    assert first.reasons == ["Gemini narrative"]
    assert second.cached is True
    assert provider.trade_calls == 1


def test_ai_service_market_summary_via_gemini(service: AIService):
    result = service.generate_market_summary(_context())
    assert result.bias == "BULLISH"
    assert result.provider == "gemini"


def test_ai_service_news_and_chat_via_gemini(service: AIService):
    news = service.summarize_news(
        [NewsItem(title="CPI cools")],
        context=_context(),
    )
    assert news.overall_sentiment == "BULLISH"

    chat = service.chat(
        [ChatMessage(role="user", content="What is bias?")],
        context=_context(),
    )
    assert chat.reply == "Echo: What is bias?"


def test_mock_provider_without_high_level_uses_transport(monkeypatch):
    """Providers without Gemini high-level methods still work via generate_text."""

    class TransportOnly:
        name = "local"

        def model_name(self):
            return "llama-test"

        def health(self):
            return True

        def generate_text(self, *, system, user, json_mode=False):
            from app.ai.schemas.responses import ProviderTextResult

            return ProviderTextResult(
                text='{"reason":["Local reason"]}',
                model="llama-test",
                provider="local",
                latency_ms=1,
            )

    cache = _MemoryCache()
    monkeypatch.setattr(ai_service_module, "response_cache", cache)
    monkeypatch.setattr(
        ai_service_module,
        "get_primary_provider",
        lambda: TransportOnly(),
    )
    monkeypatch.setattr(ai_service_module, "get_fallback_provider", lambda _p=None: None)
    monkeypatch.setattr(
        ai_service_module,
        "settings",
        SimpleNamespace(AI_MAX_RETRIES=1),
    )

    result = AIService().generate_trade_explanation(_context())
    assert result.reasons == ["Local reason"]
    assert result.provider == "local"
