"""Shared Redis client for AI caching (soft-fail)."""

from __future__ import annotations

from typing import Any

from app.core.logger import logger
from app.core.settings import settings

_redis: Any | None = None
_redis_failed = False


def get_redis() -> Any | None:
    """
    Return a Redis client or None if unavailable.

    Never raises to callers.
    """

    global _redis, _redis_failed

    if _redis_failed:
        return None
    if _redis is not None:
        return _redis

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
        _redis_failed = True
        logger.warning("Redis unavailable for AI cache: %s", exc)
        return None


def reset_redis_client() -> None:
    """Test helper to clear cached connection state."""

    global _redis, _redis_failed
    _redis = None
    _redis_failed = False
