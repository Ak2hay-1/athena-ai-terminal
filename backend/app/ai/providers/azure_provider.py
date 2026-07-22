"""
Azure OpenAI AI provider.

Azure SDK / Azure OpenAI client usage is confined to this module.
"""

from __future__ import annotations

import json
import random
import time
from typing import Any

from app.ai.prompts import chat as chat_prompt
from app.ai.prompts import market_summary as market_summary_prompt
from app.ai.prompts import news_summary as news_summary_prompt
from app.ai.prompts import trade_explanation as trade_explanation_prompt
from app.ai.providers.base import AIProvider
from app.ai.response_parser import response_parser
from app.ai.schemas.context import ChatMessage
from app.ai.schemas.context import MarketContext
from app.ai.schemas.context import NewsItem
from app.ai.schemas.responses import ChatResponse
from app.ai.schemas.responses import MarketSummary
from app.ai.schemas.responses import NewsSummary
from app.ai.schemas.responses import ProviderTextResult
from app.ai.schemas.responses import TradeExplanation
from app.ai.utils.context_filter import assert_safe_context
from app.ai.utils.cost import estimate_cost_usd
from app.ai.utils.logging_metrics import log_ai_call
from app.core.logger import logger
from app.core.settings import settings


class AzureProvider(AIProvider):
    """
    Azure OpenAI implementation (GPT-5 Mini via deployment name).

    High-level methods accept structured MarketContext only and return
    typed Athena schemas. Transport methods satisfy AIProvider for AIService.
    """

    name = "azure"

    def __init__(self) -> None:
        self.endpoint = (settings.AZURE_OPENAI_ENDPOINT or "").strip()
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.deployment = (settings.AZURE_OPENAI_DEPLOYMENT or "").strip() or "gpt-5-mini"
        self.api_version = (
            (settings.AZURE_OPENAI_API_VERSION or "").strip() or "2024-12-01-preview"
        )
        self.embed_deployment = (settings.AZURE_OPENAI_EMBED_DEPLOYMENT or "").strip()
        self.timeout = settings.AI_TIMEOUT
        self.max_retries = settings.AI_MAX_RETRIES
        self._client = None

    def model_name(self) -> str:
        return self.deployment

    def health(self) -> bool:
        if not self.api_key or not self.endpoint or not self.deployment:
            return False
        try:
            self._get_client()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # High-level Athena tasks (structured context in → typed schemas out)
    # ------------------------------------------------------------------

    def generate_trade_explanation(
        self,
        context: MarketContext,
    ) -> TradeExplanation:
        system, _ = trade_explanation_prompt.build(context)
        user = self._compact_user_prompt(
            "Explain the frozen trade plan. JSON only with reason[].",
            self._structured_context(context),
        )
        result = self.generate_text(system=system, user=user, json_mode=True)
        reasons = response_parser.parse_reasons(result.text)
        return TradeExplanation(
            reasons=reasons,
            provider=self.name,
            model=result.model,
            success=True,
        )

    def generate_market_summary(
        self,
        context: MarketContext,
    ) -> MarketSummary:
        system, _ = market_summary_prompt.build(context)
        user = self._compact_user_prompt(
            "Summarize market context. JSON: summary, bullets, bias.",
            self._structured_context(context, include_trade=False),
        )
        result = self.generate_text(system=system, user=user, json_mode=True)
        data = self._parse_json(result.text)
        return MarketSummary(
            summary=str(data.get("summary") or ""),
            bullets=self._as_str_list(data.get("bullets")),
            bias=data.get("bias"),
            provider=self.name,
            model=result.model,
            success=True,
        )

    def summarize_news(
        self,
        items: list[NewsItem],
        context: MarketContext | None = None,
    ) -> NewsSummary:
        system, _ = news_summary_prompt.build(items, context)
        payload: dict[str, Any] = {
            "symbol": context.symbol if context else None,
            "items": [
                {
                    "title": item.title,
                    "summary": item.summary,
                    "sentiment": item.sentiment,
                    "impact": item.impact,
                }
                for item in items
            ],
        }
        if context and context.news_summary:
            payload["news_summary"] = context.news_summary
        user = self._compact_user_prompt(
            "Summarize news. JSON: summary, bullets, overall_sentiment.",
            assert_safe_context(payload),
        )
        result = self.generate_text(system=system, user=user, json_mode=True)
        data = self._parse_json(result.text)
        return NewsSummary(
            summary=str(data.get("summary") or ""),
            bullets=self._as_str_list(data.get("bullets")),
            overall_sentiment=data.get("overall_sentiment"),
            provider=self.name,
            model=result.model,
            success=True,
        )

    def generate_chat_response(
        self,
        messages: list[ChatMessage],
        context: MarketContext | None = None,
    ) -> ChatResponse:
        """High-level chat returning ChatResponse (ABC chat stays transport)."""

        system = chat_prompt.build_system(context)
        trimmed = messages[-8:]
        result = self.chat(messages=trimmed, system=system)
        return ChatResponse(
            reply=result.text.strip(),
            provider=self.name,
            model=result.model,
            success=True,
        )

    # ------------------------------------------------------------------
    # AIProvider transport
    # ------------------------------------------------------------------

    def generate_text(
        self,
        *,
        system: str,
        user: str,
        json_mode: bool = False,
    ) -> ProviderTextResult:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self.deployment,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        def _call() -> ProviderTextResult:
            started = time.perf_counter()
            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0].message
            text = (choice.content or "").strip()
            if not text:
                raise ValueError("Empty response received from Azure OpenAI.")

            usage = response.usage
            prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
            completion_tokens = (
                getattr(usage, "completion_tokens", None) if usage else None
            )
            latency_ms = (time.perf_counter() - started) * 1000
            result = ProviderTextResult(
                text=text,
                model=self.deployment,
                provider=self.name,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
            self._log_transport(
                task="generate_text",
                result=result,
            )
            return result

        return self._with_backoff(_call, label="azure.generate_text")

    def chat(
        self,
        *,
        messages: list[ChatMessage],
        system: str | None = None,
    ) -> ProviderTextResult:
        client = self._get_client()
        payload: list[dict[str, str]] = []
        if system:
            payload.append({"role": "system", "content": system})
        for message in messages:
            payload.append({"role": message.role, "content": message.content})

        def _call() -> ProviderTextResult:
            started = time.perf_counter()
            response = client.chat.completions.create(
                model=self.deployment,
                messages=payload,
            )
            text = (response.choices[0].message.content or "").strip()
            if not text:
                raise ValueError("Empty chat response received from Azure OpenAI.")

            usage = response.usage
            prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
            completion_tokens = (
                getattr(usage, "completion_tokens", None) if usage else None
            )
            latency_ms = (time.perf_counter() - started) * 1000
            result = ProviderTextResult(
                text=text,
                model=self.deployment,
                provider=self.name,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
            self._log_transport(task="chat", result=result)
            return result

        return self._with_backoff(_call, label="azure.chat")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.embed_deployment:
            raise RuntimeError(
                "AZURE_OPENAI_EMBED_DEPLOYMENT is not configured."
            )

        client = self._get_client()

        def _call() -> list[list[float]]:
            response = client.embeddings.create(
                model=self.embed_deployment,
                input=texts,
            )
            ordered = sorted(response.data, key=lambda item: item.index)
            return [list(item.embedding) for item in ordered]

        return self._with_backoff(_call, label="azure.embed")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("AZURE_OPENAI_API_KEY is not configured.")
            if not self.endpoint:
                raise RuntimeError("AZURE_OPENAI_ENDPOINT is not configured.")
            if not self.deployment:
                raise RuntimeError("AZURE_OPENAI_DEPLOYMENT is not configured.")

            from openai import AzureOpenAI

            self._client = AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint.rstrip("/"),
                api_version=self.api_version,
                timeout=self.timeout,
            )
        return self._client

    def _with_backoff(self, fn, *, label: str):
        """Exponential backoff for rate limits, timeouts, and transient Azure errors."""

        last_error: Exception | None = None
        attempts = max(1, self.max_retries)
        retries_used = 0

        for attempt in range(1, attempts + 1):
            try:
                return fn()
            except Exception as exc:
                last_error = exc
                if not self._is_retryable(exc) or attempt >= attempts:
                    logger.error(
                        "azure_call failed label=%s deployment=%s attempt=%d/%d error=%s",
                        label,
                        self.deployment,
                        attempt,
                        attempts,
                        type(exc).__name__,
                    )
                    break
                retries_used = attempt
                delay = min((2 ** (attempt - 1)) + random.uniform(0, 0.5), 30.0)
                logger.warning(
                    "%s attempt %d/%d failed (%s); backoff %.1fs deployment=%s",
                    label,
                    attempt,
                    attempts,
                    type(exc).__name__,
                    delay,
                    self.deployment,
                )
                time.sleep(delay)

        assert last_error is not None
        if retries_used:
            log_ai_call(
                task=label,
                provider=self.name,
                model=self.deployment,
                latency_ms=0.0,
                retries=retries_used,
                error=str(last_error),
                deployment=self.deployment,
            )
        raise last_error

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        if status in {408, 429, 500, 502, 503, 504}:
            return True

        response = getattr(exc, "response", None)
        if response is not None:
            resp_status = getattr(response, "status_code", None)
            if resp_status in {408, 429, 500, 502, 503, 504}:
                return True

        name = type(exc).__name__.lower()
        message = str(exc).lower()
        markers = (
            "429",
            "rate limit",
            "rate_limit",
            "timeout",
            "timed out",
            "temporarily unavailable",
            "service unavailable",
            "unavailable",
            "connection reset",
            "connection aborted",
            "connection error",
            "apitimeouterror",
            "api connection",
            "503",
            "502",
            "500",
            "overloaded",
        )
        if any(marker in name for marker in ("timeout", "connection", "ratelimit")):
            return True
        return any(marker in message for marker in markers)

    def _log_transport(self, *, task: str, result: ProviderTextResult) -> None:
        log_ai_call(
            task=task,
            provider=self.name,
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
            deployment=self.deployment,
        )

    def _structured_context(
        self,
        context: MarketContext,
        *,
        include_trade: bool = True,
    ) -> dict[str, Any]:
        """Compact structured payload — never OHLC / history / order book."""

        candidate = context.trade_candidate
        payload: dict[str, Any] = {
            "trend": context.trend,
            "market_structure": context.market_structure,
            "volume": context.volume,
            "liquidity": context.liquidity,
            "order_blocks": context.order_blocks,
            "fair_value_gaps": context.fvg,
            "volatility": context.volatility,
            "confidence": candidate.confidence if candidate else None,
            "news_summary": context.news_summary,
        }
        if include_trade and candidate is not None:
            payload["trade_candidate"] = {
                "signal": candidate.signal,
                "confidence": candidate.confidence,
                "entry": candidate.entry,
                "entry_type": candidate.entry_type,
                "stop_loss": candidate.stop_loss,
                "take_profit": candidate.take_profit,
                "risk_reward": candidate.risk_reward,
                "sl_reason": candidate.sl_reason,
                "tp_reason": candidate.tp_reason,
                "entry_reason": candidate.entry_reason,
            }
        return assert_safe_context(self._drop_empty(payload))

    @staticmethod
    def _drop_empty(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: AzureProvider._drop_empty(item)
                for key, item in value.items()
                if item is not None and item != "" and item != {} and item != []
            }
        if isinstance(value, list):
            return [AzureProvider._drop_empty(item) for item in value]
        return value

    @staticmethod
    def _compact_user_prompt(instruction: str, payload: dict[str, Any]) -> str:
        body = json.dumps(payload, separators=(",", ":"), default=str)
        return f"{instruction}\n{body}"

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        try:
            extracted = response_parser._extract_json(text)
            data, _ = response_parser._loads_json(extracted)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.warning("Azure JSON parse failed: %s", type(exc).__name__)
            return {}

    @staticmethod
    def _as_str_list(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        return []
