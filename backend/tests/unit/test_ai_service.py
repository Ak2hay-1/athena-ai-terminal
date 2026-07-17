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
        symbol="BTCUSDT",
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
