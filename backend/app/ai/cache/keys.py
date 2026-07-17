"""SHA256 Redis cache key helpers for AI responses."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(state: dict[str, Any]) -> str:
    """Stable JSON serialization for hashing."""

    return json.dumps(state, sort_keys=True, separators=(",", ":"), default=str)


def build_cache_key(task: str, state: dict[str, Any]) -> str:
    """
    Build Redis key: ai:{task}:{sha256(canonical_json(state))}
    """

    digest = hashlib.sha256(canonical_json(state).encode("utf-8")).hexdigest()
    return f"ai:{task}:{digest}"
