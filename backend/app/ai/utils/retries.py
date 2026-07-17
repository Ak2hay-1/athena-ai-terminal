"""Retry helpers for AI provider calls."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from app.core.logger import logger

T = TypeVar("T")


def with_retries(
    fn: Callable[[], T],
    *,
    max_retries: int,
    label: str,
) -> T:
    """
    Execute fn with exponential backoff.

    Raises the last exception if all attempts fail.
    """

    last_error: Exception | None = None
    attempts = max(1, max_retries)

    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            logger.warning(
                "%s attempt %d/%d failed: %s",
                label,
                attempt,
                attempts,
                exc,
            )
            if attempt < attempts:
                time.sleep(min(attempt * 2, 5))

    assert last_error is not None
    raise last_error
