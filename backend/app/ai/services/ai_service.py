"""
Athena AI Service.

The ONLY class the rest of Athena should use for LLM operations.
"""

from __future__ import annotations

import time
from typing import Any

from app.ai.cache.response_cache import response_cache
from app.ai.prompts import chat as chat_prompt
from app.ai.prompts import market_summary as market_summary_prompt
from app.ai.prompts import news_summary as news_summary_prompt
from app.ai.prompts import trade_explanation as trade_explanation_prompt
from app.ai.providers.factory import get_fallback_provider
from app.ai.providers.factory import get_primary_provider
from app.ai.response_parser import response_parser
from app.ai.schemas.context import ChatMessage
from app.ai.schemas.context import MarketContext
from app.ai.schemas.context import NewsItem
from app.ai.schemas.responses import ChatResponse
from app.ai.schemas.responses import EmbeddingsResponse
from app.ai.schemas.responses import MarketSummaryResponse
from app.ai.schemas.responses import NewsSummaryResponse
from app.ai.schemas.responses import ProviderTextResult
from app.ai.schemas.responses import TradeExplanationResponse
from app.ai.utils.cost import estimate_cost_usd
from app.ai.utils.logging_metrics import log_ai_call
from app.ai.utils.retries import with_retries
from app.core.logger import logger
from app.core.settings import settings


class AIService:
    """Provider selection, prompts, cache, retries, validation, metrics."""

    def generate_trade_explanation(
        self,
        context: MarketContext,
    ) -> TradeExplanationResponse:
        task = "trade_explanation"
        state = context.cache_state()

        cached = response_cache.get(task, state, TradeExplanationResponse)
        if cached is not None:
            cached.cached = True
            log_ai_call(
                task=task,
                provider=cached.provider,
                model=cached.model,
                latency_ms=0.0,
                cache_hit=True,
            )
            return cached

        typed = self._call_high_level(
            task=task,
            method_name="generate_trade_explanation",
            call=lambda provider: provider.generate_trade_explanation(context),
        )
        if typed is not None:
            response = TradeExplanationResponse.model_validate(typed)
            if response.success and response.reasons:
                response_cache.set(task, state, response)
            return response

        system, user = trade_explanation_prompt.build(context)
        result, meta = self._generate_with_fallback(
            task=task,
            system=system,
            user=user,
            json_mode=True,
        )
        if result is None:
            response = TradeExplanationResponse(
                reasons=[],
                success=False,
                message=meta.get("error") or "AI explanation unavailable.",
                provider=meta.get("provider"),
                model=meta.get("model"),
            )
            self._log_failure(task, meta)
            return response

        reasons = response_parser.parse_reasons(result.text)
        response = TradeExplanationResponse(
            reasons=reasons,
            provider=result.provider,
            model=result.model,
            cached=False,
            success=True,
        )
        if reasons:
            response_cache.set(task, state, response)
        self._log_success(task, result, meta)
        return response

    def generate_market_summary(
        self,
        context: MarketContext,
    ) -> MarketSummaryResponse:
        task = "market_summary"
        state = context.cache_state()

        cached = response_cache.get(task, state, MarketSummaryResponse)
        if cached is not None:
            cached.cached = True
            log_ai_call(
                task=task,
                provider=cached.provider,
                model=cached.model,
                latency_ms=0.0,
                cache_hit=True,
            )
            return cached

        typed = self._call_high_level(
            task=task,
            method_name="generate_market_summary",
            call=lambda provider: provider.generate_market_summary(context),
        )
        if typed is not None:
            response = MarketSummaryResponse.model_validate(typed)
            if response.success:
                response_cache.set(task, state, response)
            return response

        system, user = market_summary_prompt.build(context)
        result, meta = self._generate_with_fallback(
            task=task,
            system=system,
            user=user,
            json_mode=True,
        )
        if result is None:
            response = MarketSummaryResponse(
                success=False,
                message=meta.get("error") or "Market summary unavailable.",
                provider=meta.get("provider"),
                model=meta.get("model"),
            )
            self._log_failure(task, meta)
            return response

        data = self._parse_json_object(result.text)
        response = MarketSummaryResponse(
            summary=str(data.get("summary") or ""),
            bullets=self._as_str_list(data.get("bullets")),
            bias=data.get("bias"),
            provider=result.provider,
            model=result.model,
            success=True,
        )
        response_cache.set(task, state, response)
        self._log_success(task, result, meta)
        return response

    def summarize_news(
        self,
        items: list[NewsItem],
        context: MarketContext | None = None,
    ) -> NewsSummaryResponse:
        task = "news_summary"
        state = {
            "symbol": context.symbol if context else None,
            "titles": [item.title for item in items],
            "sentiments": [item.sentiment for item in items],
        }

        cached = response_cache.get(task, state, NewsSummaryResponse)
        if cached is not None:
            cached.cached = True
            log_ai_call(
                task=task,
                provider=cached.provider,
                model=cached.model,
                latency_ms=0.0,
                cache_hit=True,
            )
            return cached

        if not items:
            return NewsSummaryResponse(
                summary="No news items provided.",
                bullets=[],
                overall_sentiment="NEUTRAL",
                success=True,
            )

        typed = self._call_high_level(
            task=task,
            method_name="summarize_news",
            call=lambda provider: provider.summarize_news(items, context),
        )
        if typed is not None:
            response = NewsSummaryResponse.model_validate(typed)
            if response.success:
                response_cache.set(task, state, response)
            return response

        system, user = news_summary_prompt.build(items, context)
        result, meta = self._generate_with_fallback(
            task=task,
            system=system,
            user=user,
            json_mode=True,
        )
        if result is None:
            response = NewsSummaryResponse(
                success=False,
                message=meta.get("error") or "News summary unavailable.",
                provider=meta.get("provider"),
                model=meta.get("model"),
            )
            self._log_failure(task, meta)
            return response

        data = self._parse_json_object(result.text)
        response = NewsSummaryResponse(
            summary=str(data.get("summary") or ""),
            bullets=self._as_str_list(data.get("bullets")),
            overall_sentiment=data.get("overall_sentiment"),
            provider=result.provider,
            model=result.model,
            success=True,
        )
        response_cache.set(task, state, response)
        self._log_success(task, result, meta)
        return response

    def chat(
        self,
        messages: list[ChatMessage],
        context: MarketContext | None = None,
    ) -> ChatResponse:
        task = "chat"
        if not messages:
            return ChatResponse(
                success=False,
                message="At least one chat message is required.",
            )

        # Do not cache chat — conversational and user-specific.
        typed = self._call_high_level(
            task=task,
            method_name="generate_chat_response",
            call=lambda provider: provider.generate_chat_response(messages, context),
        )
        if typed is not None:
            return ChatResponse.model_validate(typed)

        system = chat_prompt.build_system(context)
        result, meta = self._chat_with_fallback(
            task=task,
            messages=messages,
            system=system,
        )
        if result is None:
            response = ChatResponse(
                success=False,
                message=meta.get("error") or "Chat unavailable.",
                provider=meta.get("provider"),
                model=meta.get("model"),
            )
            self._log_failure(task, meta)
            return response

        response = ChatResponse(
            reply=result.text.strip(),
            provider=result.provider,
            model=result.model,
            success=True,
        )
        self._log_success(task, result, meta)
        return response

    def generate_embeddings(self, texts: list[str]) -> EmbeddingsResponse:
        task = "embeddings"
        cleaned = [text.strip() for text in texts if text and text.strip()]
        if not cleaned:
            return EmbeddingsResponse(
                success=False,
                message="At least one non-empty text is required.",
            )

        started = time.perf_counter()
        provider = get_primary_provider()
        fallback_used = False
        retries = 0
        error: str | None = None

        try:
            vectors = with_retries(
                lambda: provider.embed(cleaned),
                max_retries=settings.AI_MAX_RETRIES,
                label=f"{provider.name}.embed",
            )
        except Exception as primary_exc:
            error = str(primary_exc)
            retries = settings.AI_MAX_RETRIES
            fallback = get_fallback_provider(provider)
            if fallback is None:
                log_ai_call(
                    task=task,
                    provider=provider.name,
                    model=provider.model_name(),
                    latency_ms=(time.perf_counter() - started) * 1000,
                    retries=retries,
                    error=error,
                )
                return EmbeddingsResponse(
                    success=False,
                    message=error,
                    provider=provider.name,
                    model=provider.model_name(),
                )
            try:
                vectors = with_retries(
                    lambda: fallback.embed(cleaned),
                    max_retries=settings.AI_MAX_RETRIES,
                    label=f"{fallback.name}.embed",
                )
                provider = fallback
                fallback_used = True
                error = None
            except Exception as fallback_exc:
                error = str(fallback_exc)
                log_ai_call(
                    task=task,
                    provider=fallback.name,
                    model=fallback.model_name(),
                    latency_ms=(time.perf_counter() - started) * 1000,
                    retries=retries,
                    fallback_used=True,
                    error=error,
                )
                return EmbeddingsResponse(
                    success=False,
                    message=error,
                    provider=fallback.name,
                    model=fallback.model_name(),
                )

        dimensions = len(vectors[0]) if vectors else 0
        log_ai_call(
            task=task,
            provider=provider.name,
            model=provider.model_name(),
            latency_ms=(time.perf_counter() - started) * 1000,
            retries=retries,
            fallback_used=fallback_used,
            error=error,
            dimensions=dimensions,
            count=len(vectors),
        )
        return EmbeddingsResponse(
            embeddings=vectors,
            dimensions=dimensions,
            provider=provider.name,
            model=provider.model_name(),
            success=True,
        )

    def _call_high_level(
        self,
        *,
        task: str,
        method_name: str,
        call,
    ) -> Any | None:
        """
        Prefer provider high-level methods (e.g. Gemini) when available.

        Returns a typed response model on success, otherwise None so the
        transport-level path can run (including local fallback).
        """

        primary = get_primary_provider()
        method = getattr(primary, method_name, None)
        if not callable(method):
            return None

        started = time.perf_counter()
        try:
            result = call(primary)
            log_ai_call(
                task=task,
                provider=getattr(result, "provider", primary.name),
                model=getattr(result, "model", primary.model_name()),
                latency_ms=(time.perf_counter() - started) * 1000,
                cache_hit=False,
                fallback_used=False,
            )
            return result
        except Exception as primary_exc:
            logger.warning(
                "AI %s high-level %s.%s failed: %s",
                task,
                primary.name,
                method_name,
                primary_exc,
            )

        fallback = get_fallback_provider(primary)
        if fallback is None:
            return None
        method = getattr(fallback, method_name, None)
        if not callable(method):
            return None

        try:
            result = call(fallback)
            log_ai_call(
                task=task,
                provider=getattr(result, "provider", fallback.name),
                model=getattr(result, "model", fallback.model_name()),
                latency_ms=(time.perf_counter() - started) * 1000,
                cache_hit=False,
                fallback_used=True,
            )
            return result
        except Exception as fallback_exc:
            logger.warning(
                "AI %s high-level fallback %s.%s failed: %s",
                task,
                fallback.name,
                method_name,
                fallback_exc,
            )
            return None

    def _generate_with_fallback(
        self,
        *,
        task: str,
        system: str,
        user: str,
        json_mode: bool,
    ) -> tuple[ProviderTextResult | None, dict[str, Any]]:
        primary = get_primary_provider()
        meta: dict[str, Any] = {
            "provider": primary.name,
            "model": primary.model_name(),
            "retries": 0,
            "fallback_used": False,
            "error": None,
        }

        try:
            result = with_retries(
                lambda: primary.generate_text(
                    system=system,
                    user=user,
                    json_mode=json_mode,
                ),
                max_retries=settings.AI_MAX_RETRIES,
                label=f"{primary.name}.generate_text",
            )
            return result, meta
        except Exception as primary_exc:
            meta["retries"] = settings.AI_MAX_RETRIES
            meta["error"] = str(primary_exc)
            logger.warning(
                "AI %s primary provider failed: %s",
                task,
                primary_exc,
            )

        fallback = get_fallback_provider(primary)
        if fallback is None:
            return None, meta

        meta["fallback_used"] = True
        meta["provider"] = fallback.name
        meta["model"] = fallback.model_name()
        try:
            result = with_retries(
                lambda: fallback.generate_text(
                    system=system,
                    user=user,
                    json_mode=json_mode,
                ),
                max_retries=settings.AI_MAX_RETRIES,
                label=f"{fallback.name}.generate_text",
            )
            meta["error"] = None
            return result, meta
        except Exception as fallback_exc:
            meta["error"] = str(fallback_exc)
            logger.warning(
                "AI %s fallback provider failed: %s",
                task,
                fallback_exc,
            )
            return None, meta

    def _chat_with_fallback(
        self,
        *,
        task: str,
        messages: list[ChatMessage],
        system: str,
    ) -> tuple[ProviderTextResult | None, dict[str, Any]]:
        primary = get_primary_provider()
        meta: dict[str, Any] = {
            "provider": primary.name,
            "model": primary.model_name(),
            "retries": 0,
            "fallback_used": False,
            "error": None,
        }

        try:
            result = with_retries(
                lambda: primary.chat(messages=messages, system=system),
                max_retries=settings.AI_MAX_RETRIES,
                label=f"{primary.name}.chat",
            )
            return result, meta
        except Exception as primary_exc:
            meta["retries"] = settings.AI_MAX_RETRIES
            meta["error"] = str(primary_exc)
            logger.warning("AI %s primary chat failed: %s", task, primary_exc)

        fallback = get_fallback_provider(primary)
        if fallback is None:
            return None, meta

        meta["fallback_used"] = True
        meta["provider"] = fallback.name
        meta["model"] = fallback.model_name()
        try:
            result = with_retries(
                lambda: fallback.chat(messages=messages, system=system),
                max_retries=settings.AI_MAX_RETRIES,
                label=f"{fallback.name}.chat",
            )
            meta["error"] = None
            return result, meta
        except Exception as fallback_exc:
            meta["error"] = str(fallback_exc)
            logger.warning("AI %s fallback chat failed: %s", task, fallback_exc)
            return None, meta

    def _parse_json_object(self, text: str) -> dict[str, Any]:
        try:
            extracted = response_parser._extract_json(text)
            data, _ = response_parser._loads_json(extracted)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.warning("Failed to parse AI JSON object: %s", exc)
            return {}

    @staticmethod
    def _as_str_list(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        return []

    def _log_success(
        self,
        task: str,
        result: ProviderTextResult,
        meta: dict[str, Any],
    ) -> None:
        log_ai_call(
            task=task,
            provider=result.provider,
            model=result.model,
            latency_ms=result.latency_ms,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            cost_usd_estimate=estimate_cost_usd(
                result.model,
                result.prompt_tokens,
                result.completion_tokens,
            ),
            cache_hit=False,
            retries=int(meta.get("retries") or 0),
            fallback_used=bool(meta.get("fallback_used")),
        )

    def _log_failure(self, task: str, meta: dict[str, Any]) -> None:
        log_ai_call(
            task=task,
            provider=meta.get("provider"),
            model=meta.get("model"),
            latency_ms=0.0,
            cache_hit=False,
            retries=int(meta.get("retries") or 0),
            fallback_used=bool(meta.get("fallback_used")),
            error=meta.get("error"),
        )


ai_service = AIService()
