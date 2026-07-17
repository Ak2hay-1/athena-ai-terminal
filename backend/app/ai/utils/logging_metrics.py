"""Structured AI call logging."""

from __future__ import annotations

from typing import Any

from app.core.logger import logger


def log_ai_call(
    *,
    task: str,
    provider: str | None,
    model: str | None,
    latency_ms: float,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    cost_usd_estimate: float | None = None,
    cache_hit: bool = False,
    retries: int = 0,
    fallback_used: bool = False,
    error: str | None = None,
    **extra: Any,
) -> None:
    """Emit a single structured AI metrics log line."""

    payload = {
        "task": task,
        "provider": provider,
        "model": model,
        "latency_ms": round(latency_ms, 2),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd_estimate": cost_usd_estimate,
        "cache_hit": cache_hit,
        "retries": retries,
        "fallback_used": fallback_used,
        "error": error,
        **extra,
    }
    logger.info("ai_call %s", payload)
