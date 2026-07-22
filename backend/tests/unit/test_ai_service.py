"""Tests for AIService cache, fallback, and typed responses."""

from __future__ import annotations

import importlib

from app.ai.schemas.context import MarketContext
from app.ai.schemas.context import TradeCandidate
from app.ai.schemas.responses import ProviderTextResult
from app.ai.services.ai_service import AIService

ai_service_module = importlib.import_module("app.ai.services.ai_service")


class _FakeProvider:
    name = "fake"

    def __init__(self, text: str = '{"reason":["Cached narrative"]}') -> None:
        self.text = text
        self.calls = 0

    def model_name(self) -> str:
        return "fake-model"

    def health(self) -> bool:
        return True

    def generate_text(self, *, system: str, user: str, json_mode: bool = False):
        self.calls += 1
        return ProviderTextResult(
            text=self.text,
            model=self.model_name(),
            provider=self.name,
            latency_ms=12.0,
            prompt_tokens=10,
            completion_tokens=20,
        )

    def chat(self, *, messages, system=None):
        raise NotImplementedError

    def embed(self, texts):
        raise NotImplementedError


class _FailProvider(_FakeProvider):
    name = "fail"

    def generate_text(self, *, system: str, user: str, json_mode: bool = False):
        self.calls += 1
        raise RuntimeError("primary down")


class _MemoryCache:
    def __init__(self) -> None:
        self.store: dict[str, object] = {}

    def get(self, task, state, model):
        key = f"{task}:{state.get('symbol')}:{state.get('confidence')}"
        value = self.store.get(key)
        if value is None:
            return None
        return model.model_validate(value)  # type: ignore[attr-defined]

    def set(self, task, state, value):
        key = f"{task}:{state.get('symbol')}:{state.get('confidence')}"
        self.store[key] = value.model_dump()


def _context() -> MarketContext:
    return MarketContext(
        symbol="XAUUSD",
        timeframe="1H",
        trend="Bullish",
        trade_candidate=TradeCandidate(
            signal="BUY",
            confidence=88,
        ),
    )


def test_generate_trade_explanation_cache_hit(monkeypatch):
    service = AIService()
    cache = _MemoryCache()
    provider = _FakeProvider()
    monkeypatch.setattr(ai_service_module, "response_cache", cache)
    monkeypatch.setattr(ai_service_module, "get_primary_provider", lambda: provider)
    monkeypatch.setattr(ai_service_module, "get_fallback_provider", lambda _p=None: None)
    monkeypatch.setattr(ai_service_module, "settings", type("S", (), {"AI_MAX_RETRIES": 1})())

    first = service.generate_trade_explanation(_context())
    second = service.generate_trade_explanation(_context())

    assert first.success is True
    assert first.reasons == ["Cached narrative"]
    assert second.cached is True
    assert provider.calls == 1


def test_generate_trade_explanation_falls_back(monkeypatch):
    service = AIService()
    cache = _MemoryCache()
    primary = _FailProvider()
    fallback = _FakeProvider(text='{"reason":["From local"]}')
    monkeypatch.setattr(ai_service_module, "response_cache", cache)
    monkeypatch.setattr(ai_service_module, "get_primary_provider", lambda: primary)
    monkeypatch.setattr(
        ai_service_module,
        "get_fallback_provider",
        lambda _p=None: fallback,
    )
    monkeypatch.setattr(ai_service_module, "settings", type("S", (), {"AI_MAX_RETRIES": 1})())

    result = service.generate_trade_explanation(_context())
    assert result.success is True
    assert result.reasons == ["From local"]
    assert result.provider == "fake"
    assert primary.calls == 1
    assert fallback.calls == 1


def test_factory_resolves_local():
    from app.ai.providers.factory import resolve_provider

    provider = resolve_provider("local")
    assert provider.name == "local"


def test_chat_redirects_decision_request(monkeypatch):
    service = AIService()
    provider = _FakeProvider()
    monkeypatch.setattr(ai_service_module, "get_primary_provider", lambda: provider)
    monkeypatch.setattr(ai_service_module, "get_fallback_provider", lambda _p=None: None)

    from app.ai.schemas.context import ChatMessage

    result = service.chat(
        [ChatMessage(role="user", content="Should I BUY XAUUSD right now?")]
    )
    assert result.success is True
    assert result.redirected is True
    assert provider.calls == 0
    assert "deterministic engine" in result.reply.lower()


def test_explain_indicator_and_cache(monkeypatch):
    service = AIService()
    cache = _MemoryCache()
    # Override memory cache keying for indicator task
    cache.get = lambda task, state, model: (  # type: ignore[method-assign]
        model.model_validate(cache.store[f"{task}:{state.get('topic')}"])
        if f"{task}:{state.get('topic')}" in cache.store
        else None
    )
    cache.set = lambda task, state, value: cache.store.__setitem__(  # type: ignore[method-assign]
        f"{task}:{state.get('topic')}",
        value.model_dump(),
    )

    provider = _FakeProvider(
        text=(
            '{"topic":"fvg","summary":"Fair value gap",'
            '"how_it_works":["Imbalance"],"athena_usage":"Confluence",'
            '"pitfalls":["Chasing"]}'
        )
    )
    monkeypatch.setattr(ai_service_module, "response_cache", cache)
    monkeypatch.setattr(ai_service_module, "get_primary_provider", lambda: provider)
    monkeypatch.setattr(ai_service_module, "get_fallback_provider", lambda _p=None: None)
    monkeypatch.setattr(ai_service_module, "settings", type("S", (), {"AI_MAX_RETRIES": 1})())

    first = service.explain_indicator("fvg", _context())
    second = service.explain_indicator("fvg", _context())
    assert first.success is True
    assert first.summary == "Fair value gap"
    assert second.cached is True
    assert provider.calls == 1


def test_teach_strategy_parses_lesson(monkeypatch):
    service = AIService()
    cache = _MemoryCache()
    cache.get = lambda task, state, model: None  # type: ignore[method-assign]
    cache.set = lambda task, state, value: None  # type: ignore[method-assign]
    provider = _FakeProvider(
        text=(
            '{"topic":"smc","title":"SMC","lesson":"Structure first",'
            '"key_points":["BOS"],"exercise":"Mark BOS",'
            '"common_mistakes":["FOMO"]}'
        )
    )
    monkeypatch.setattr(ai_service_module, "response_cache", cache)
    monkeypatch.setattr(ai_service_module, "get_primary_provider", lambda: provider)
    monkeypatch.setattr(ai_service_module, "get_fallback_provider", lambda _p=None: None)
    monkeypatch.setattr(ai_service_module, "settings", type("S", (), {"AI_MAX_RETRIES": 1})())

    result = service.teach_strategy("smc")
    assert result.success is True
    assert result.title == "SMC"
    assert "Structure" in result.lesson


def test_summarize_session_parses(monkeypatch):
    service = AIService()
    cache = _MemoryCache()
    cache.get = lambda task, state, model: None  # type: ignore[method-assign]
    cache.set = lambda task, state, value: None  # type: ignore[method-assign]
    provider = _FakeProvider(
        text=(
            '{"summary":"Quiet session","highlights":["One FVG"],'
            '"risk_notes":["News"],"lessons":["Wait"]}'
        )
    )
    monkeypatch.setattr(ai_service_module, "response_cache", cache)
    monkeypatch.setattr(ai_service_module, "get_primary_provider", lambda: provider)
    monkeypatch.setattr(ai_service_module, "get_fallback_provider", lambda _p=None: None)
    monkeypatch.setattr(ai_service_module, "settings", type("S", (), {"AI_MAX_RETRIES": 1})())

    result = service.summarize_session(
        {"mode": "session", "symbol": "XAUUSD", "total_recommendations": 3}
    )
    assert result.success is True
    assert result.summary == "Quiet session"
    assert result.highlights == ["One FVG"]


def test_chat_stream_yields_tokens(monkeypatch):
    service = AIService()

    class _StreamProvider(_FakeProvider):
        def chat_stream(self, *, messages, system=None):
            yield "Hel"
            yield "lo"

    provider = _StreamProvider()
    monkeypatch.setattr(ai_service_module, "get_primary_provider", lambda: provider)
    monkeypatch.setattr(ai_service_module, "get_fallback_provider", lambda _p=None: None)

    from app.ai.schemas.context import ChatMessage

    chunks = list(
        service.chat_stream([ChatMessage(role="user", content="Explain trend")])
    )
    assert "".join(chunks) == "Hello"
