"""
Google Gemini AI provider.

The google-genai SDK is imported only in this module.
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
from app.core.logger import logger
from app.core.settings import settings


class GeminiProvider(AIProvider):
    """
    Gemini implementation.

    High-level methods accept structured MarketContext only and return
    typed schemas. Transport methods satisfy AIProvider for AIService.
    """

    name = "gemini"

    def __init__(self) -> None:
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.embed_model = settings.GEMINI_EMBED_MODEL
        self.timeout = settings.AI_TIMEOUT
        self.max_retries = settings.AI_MAX_RETRIES
        self._client = None

    def model_name(self) -> str:
        return self.model

    def health(self) -> bool:
        if not self.api_key:
            return False
        try:
            self._get_client()
            return True
        except Exception as exc:
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
        # Cap history to last 8 turns for token efficiency.
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
        from google.genai import types

        client = self._get_client()
        config_kwargs: dict[str, Any] = {
            "system_instruction": system,
        }
        if json_mode:
            config_kwargs["response_mime_type"] = "application/json"

        def _call() -> ProviderTextResult:
            started = time.perf_counter()
            response = client.models.generate_content(
                model=self.model,
                contents=user,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            text = (response.text or "").strip()
            if not text:
                raise ValueError("Empty response received from Gemini.")

            prompt_tokens = None
            completion_tokens = None
            usage = getattr(response, "usage_metadata", None)
            if usage is not None:
                prompt_tokens = getattr(usage, "prompt_token_count", None)
                completion_tokens = getattr(usage, "candidates_token_count", None)

            return ProviderTextResult(
                text=text,
                model=self.model,
                provider=self.name,
                latency_ms=(time.perf_counter() - started) * 1000,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

        return self._with_backoff(_call, label="gemini.generate_text")

    def chat(
        self,
        *,
        messages: list[ChatMessage],
        system: str | None = None,
    ) -> ProviderTextResult:
        from google.genai import types

        client = self._get_client()
        contents = []
        for message in messages:
            role = "model" if message.role == "assistant" else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=message.content)],
                )
            )

        config = None
        if system:
            config = types.GenerateContentConfig(system_instruction=system)

        def _call() -> ProviderTextResult:
            started = time.perf_counter()
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            text = (response.text or "").strip()
            if not text:
                raise ValueError("Empty chat response received from Gemini.")

            prompt_tokens = None
            completion_tokens = None
            usage = getattr(response, "usage_metadata", None)
            if usage is not None:
                prompt_tokens = getattr(usage, "prompt_token_count", None)
                completion_tokens = getattr(usage, "candidates_token_count", None)

            return ProviderTextResult(
                text=text,
                model=self.model,
                provider=self.name,
                latency_ms=(time.perf_counter() - started) * 1000,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

        return self._with_backoff(_call, label="gemini.chat")

    def embed(self, texts: list[str]) -> list[list[float]]:
        from google.genai import types

        client = self._get_client()

        def _call() -> list[list[float]]:
            result = client.models.embed_content(
                model=self.embed_model,
                contents=texts,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            embeddings = getattr(result, "embeddings", None) or []
            vectors: list[list[float]] = []
            for item in embeddings:
                values = getattr(item, "values", None)
                if values is None:
                    raise ValueError("Invalid embedding payload from Gemini.")
                vectors.append([float(value) for value in values])
            if len(vectors) != len(texts):
                raise ValueError("Gemini embedding count mismatch.")
            return vectors

        return self._with_backoff(_call, label="gemini.embed")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("GEMINI_API_KEY is not configured.")
            from google import genai
            from google.genai import types


            retry_options = types.HttpRetryOptions(
                initial_delay=1.0,
                attempts=max(2, self.max_retries + 1),
                exp_base=2.0,
                max_delay=30.0,
                http_status_codes=[408, 429, 500, 502, 503, 504],
            )
            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(
                    timeout=self.timeout * 1000,
                    retry_options=retry_options,
                ),
            )
        return self._client

    def _with_backoff(self, fn, *, label: str):
        """
        Application-level exponential backoff for 429 / timeouts / transient errors.

        Complements SDK HttpRetryOptions.
        """

        last_error: Exception | None = None
        attempts = max(1, self.max_retries)

        for attempt in range(1, attempts + 1):
            try:
                return fn()
            except Exception as exc:
                last_error = exc
                if not self._is_retryable(exc) or attempt >= attempts:
                    break
                delay = min((2 ** (attempt - 1)) + random.uniform(0, 0.5), 30.0)
                logger.warning(
                    "%s attempt %d/%d failed (%s); backoff %.1fs",
                    label,
                    attempt,
                    attempts,
                    exc,
                    delay,
                )
                time.sleep(delay)

        assert last_error is not None
        raise last_error

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if code in {408, 429, 500, 502, 503, 504}:
            return True

        name = type(exc).__name__.lower()
        message = str(exc).lower()
        markers = (
            "429",
            "resource exhausted",
            "resource_exhausted",
            "rate limit",
            "timeout",
            "timed out",
            "temporarily unavailable",
            "unavailable",
            "503",
            "502",
            "500",
            "connection reset",
            "connection aborted",
        )
        if any(marker in name for marker in ("timeout", "unavailable", "server")):
            return True
        return any(marker in message for marker in markers)

    def _structured_context(
        self,
        context: MarketContext,
        *,
        include_trade: bool = True,
    ) -> dict[str, Any]:
        """
        Compact structured payload — never OHLC / history / order book.
        """

        candidate = context.trade_candidate
        payload: dict[str, Any] = {
            "trend": context.trend,
            "market_structure": context.market_structure,
            "volume": context.volume,
            "liquidity": context.liquidity,
            "order_blocks": context.order_blocks,
            "fvgs": context.fvg,
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
        # Drop empty / null leaves to save tokens
        return assert_safe_context(self._drop_empty(payload))

    @staticmethod
    def _drop_empty(value: Any) -> Any:
        if isinstance(value, dict):
            cleaned = {
                key: GeminiProvider._drop_empty(item)
                for key, item in value.items()
                if item is not None and item != "" and item != {} and item != []
            }
            return cleaned
        if isinstance(value, list):
            return [GeminiProvider._drop_empty(item) for item in value]
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
            logger.warning("Gemini JSON parse failed: %s", exc)
            return {}

    @staticmethod
    def _as_str_list(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        return []
