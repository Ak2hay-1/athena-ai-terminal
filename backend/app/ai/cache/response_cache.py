"""Redis-backed AI response cache with soft-fail semantics."""

from __future__ import annotations

import json
from typing import Any
from typing import TypeVar

from pydantic import BaseModel

from app.ai.cache.keys import build_cache_key
from app.ai.cache.redis_client import get_redis
from app.core.logger import logger
from app.core.settings import settings

T = TypeVar("T", bound=BaseModel)


class ResponseCache:
    """Get/set typed AI responses in Redis."""

    def get(self, task: str, state: dict[str, Any], model: type[T]) -> T | None:
        client = get_redis()
        if client is None:
            return None

        key = build_cache_key(task, state)
        try:
            raw = client.get(key)
            if not raw:
                return None
            data = json.loads(raw)
            return model.model_validate(data)
        except Exception as exc:
            logger.warning("AI cache get failed: %s", exc)
            return None

    def set(self, task: str, state: dict[str, Any], value: BaseModel) -> None:
        client = get_redis()
        if client is None:
            return

        key = build_cache_key(task, state)
        try:
            client.setex(
                key,
                settings.AI_CACHE_TTL_SECONDS,
                value.model_dump_json(),
            )
        except Exception as exc:
            logger.warning("AI cache set failed: %s", exc)


response_cache = ResponseCache()
