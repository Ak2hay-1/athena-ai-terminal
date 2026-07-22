"""Structured [CACHE] log helpers for performance debugging."""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger("athena.cache")


def cache_log(event: str, **fields: object) -> None:
    """
    Emit a single-line cache event.

    Example::

        [CACHE] RAM HIT symbol=EURUSD timeframe=M5 limit=500
    """

    parts = " ".join(f"{key}={value}" for key, value in fields.items())
    if parts:
        logger.info("[CACHE] %s %s", event, parts)
    else:
        logger.info("[CACHE] %s", event)
