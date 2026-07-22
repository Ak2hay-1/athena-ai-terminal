"""
Thin AI client for agent reasoning — wraps ai_service with retries/fallback.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.ai.services.ai_service import ai_service
from app.ai.utils.cost import estimate_cost_usd
from app.ai.utils.logging_metrics import log_ai_call
from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger("athena.ai.client")


class AIClient:
    """
    Async-friendly facade over AIService for JSON generation.
    """

    async def generate_json(
        self,
        *,
        system: str,
        user: str,
        task: str = "setup_reasoning",
    ) -> dict[str, Any]:
        max_retries = max(0, int(settings.REASONING_MAX_RETRIES))

        def _call() -> dict[str, Any]:
            result, meta = ai_service._generate_with_fallback(
                task=task,
                system=system,
                user=user,
                json_mode=True,
            )
            if result is None:
                return {
                    "success": False,
                    "error": meta.get("error") or "AI unavailable",
                    "provider": meta.get("provider"),
                    "model": meta.get("model"),
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "latency_ms": 0.0,
                    "cost_usd": 0.0,
                    "data": {},
                }

            data = ai_service._parse_json_object(result.text)
            prompt_tokens = int(result.prompt_tokens or 0)
            completion_tokens = int(result.completion_tokens or 0)
            cost = estimate_cost_usd(
                result.model,
                prompt_tokens,
                completion_tokens,
            )
            log_ai_call(
                task=task,
                provider=result.provider,
                model=result.model,
                latency_ms=float(result.latency_ms or 0.0),
                cache_hit=False,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd_estimate=cost,
            )
            return {
                "success": True,
                "data": data,
                "provider": result.provider,
                "model": result.model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "latency_ms": float(result.latency_ms or 0.0),
                "cost_usd": cost or 0.0,
            }

        last: dict[str, Any] = {"success": False, "error": "not_attempted", "data": {}}
        attempts = max_retries + 1
        for attempt in range(attempts):
            last = await asyncio.to_thread(_call)
            if last.get("success"):
                return last
            logger.warning(
                "ai_client action=generate_json task=%s attempt=%s error=%s",
                task,
                attempt + 1,
                last.get("error"),
            )
        return last


ai_client = AIClient()
