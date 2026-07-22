"""Shared Redis client for AI caching and live market state (soft-fail)."""

from __future__ import annotations

import time
from typing import Any

from app.core.logger import logger
from app.core.settings import settings

_redis: Any | None = None
_next_retry_at = 0.0

# After a failure, wait this long before probing Redis again so a down
# server cannot add latency to every call, while still recovering
# automatically once Redis is back.
_RETRY_COOLDOWN_S = 30.0


def get_redis() -> Any | None:
    """
    Return a Redis client or None if unavailable.

    Never raises to callers. Reconnects automatically (with a cooldown)
    after outages.
    """

    global _redis, _next_retry_at

    if _redis is not None:
        return _redis
    if time.monotonic() < _next_retry_at:
        return None

    try:
        import redis

        client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1.5,
            socket_timeout=1.5,
        )
        client.ping()
        _redis = client
        return _redis
    except Exception as exc:
        _next_retry_at = time.monotonic() + _RETRY_COOLDOWN_S
        logger.warning("Redis unavailable: %s", exc)
        return None


def invalidate_redis_client() -> None:
    """Drop the cached client after a connection error mid-use."""

    global _redis, _next_retry_at
    _redis = None
    _next_retry_at = time.monotonic() + _RETRY_COOLDOWN_S


def reset_redis_client() -> None:
    """Test helper to clear cached connection state."""

    global _redis, _next_retry_at
    _redis = None
    _next_retry_at = 0.0
