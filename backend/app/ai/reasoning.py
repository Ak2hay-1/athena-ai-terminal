"""
Setup reasoning engine — interprets evidence via Azure GPT-5 Mini (when configured).
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from typing import Any

from app.ai.client import AIClient
from app.ai.client import ai_client
from app.ai.prompts import setup_reasoning as setup_reasoning_prompt
from app.ai.schemas.responses import SetupReasoningResponse
from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger("athena.ai.reasoning")


def should_run_reasoning(validation_payload: dict[str, Any]) -> bool:
    if not settings.REASONING_ENABLED:
        return False
    status = str(validation_payload.get("status") or "").upper()
    min_status = str(settings.REASONING_MIN_STATUS or "APPROVED").upper()
    if status != min_status:
        return False
    confluence = float(validation_payload.get("confluence") or 0.0)
    return confluence >= float(settings.REASONING_MIN_CONFLUENCE)


class SetupReasoningEngine:
    """
    Evidence-only reasoning with response cache.
    """

    def __init__(self, client: AIClient | None = None) -> None:
        self._client = client or ai_client
        self._cache: OrderedDict[str, tuple[float, SetupReasoningResponse]] = OrderedDict()

    def _cache_key(
        self,
        evidence: dict[str, Any],
        similar_trades: dict[str, Any] | None,
    ) -> str:
        blob = json.dumps(
            {"evidence": evidence, "similar": similar_trades or {}},
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _cache_get(self, key: str) -> SetupReasoningResponse | None:
        item = self._cache.get(key)
        if item is None:
            return None
        ts, response = item
        ttl = max(1, int(settings.REASONING_CACHE_TTL_SECONDS))
        if time.time() - ts > ttl:
            self._cache.pop(key, None)
            return None
        self._cache.move_to_end(key)
        return response

    def _cache_put(self, key: str, response: SetupReasoningResponse) -> None:
        self._cache[key] = (time.time(), response)
        self._cache.move_to_end(key)
        while len(self._cache) > 256:
            self._cache.popitem(last=False)

    async def reason(
        self,
        evidence: dict[str, Any],
        similar_trades: dict[str, Any] | None = None,
    ) -> SetupReasoningResponse:
        key = self._cache_key(evidence, similar_trades)
        cached = self._cache_get(key)
        if cached is not None:
            clone = cached.model_copy()
            clone.cached = True
            return clone

        system, user = setup_reasoning_prompt.build(evidence, similar_trades)
        result = await self._client.generate_json(
            system=system,
            user=user,
            task="setup_reasoning",
        )
        if not result.get("success"):
            return SetupReasoningResponse(
                success=False,
                message=str(result.get("error") or "Reasoning unavailable"),
                provider=result.get("provider"),
                model=result.get("model"),
            )

        data = result.get("data") or {}
        response = SetupReasoningResponse(
            summary=str(data.get("summary") or ""),
            institutional_reasoning=str(data.get("institutional_reasoning") or ""),
            potential_risks=_as_str_list(data.get("potential_risks")),
            alternative_scenarios=_as_str_list(data.get("alternative_scenarios")),
            confidence_explanation=str(data.get("confidence_explanation") or ""),
            what_to_watch=_as_str_list(data.get("what_to_watch")),
            evidence_citations=_as_str_list(data.get("evidence_citations")),
            similar_trades=similar_trades,
            provider=result.get("provider"),
            model=result.get("model"),
            success=True,
            prompt_tokens=result.get("prompt_tokens"),
            completion_tokens=result.get("completion_tokens"),
            latency_ms=result.get("latency_ms"),
            cost_usd=result.get("cost_usd"),
        )
        self._cache_put(key, response)
        logger.info(
            "reasoning action=complete provider=%s model=%s latency_ms=%s",
            response.provider,
            response.model,
            response.latency_ms,
        )
        return response


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


setup_reasoning_engine = SetupReasoningEngine()
