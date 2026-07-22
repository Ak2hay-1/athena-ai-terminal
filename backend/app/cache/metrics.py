"""Thread-safe cache hit/miss counters."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from dataclasses import field


@dataclass
class CacheMetrics:
    """Aggregate counters exposed via CacheManager.metrics()."""

    ram_hits: int = 0
    ram_misses: int = 0
    db_hits: int = 0
    db_misses: int = 0
    indicator_hits: int = 0
    indicator_misses: int = 0
    ai_hits: int = 0
    ai_misses: int = 0
    sync_runs: int = 0
    sync_candles: int = 0
    preloads_started: int = 0
    preloads_completed: int = 0
    invalidations: int = 0
    started_at: float = field(default_factory=time.monotonic)

    def snapshot(self) -> dict[str, float | int]:
        elapsed = max(0.001, time.monotonic() - self.started_at)
        return {
            "ram_hits": self.ram_hits,
            "ram_misses": self.ram_misses,
            "db_hits": self.db_hits,
            "db_misses": self.db_misses,
            "indicator_hits": self.indicator_hits,
            "indicator_misses": self.indicator_misses,
            "ai_hits": self.ai_hits,
            "ai_misses": self.ai_misses,
            "sync_runs": self.sync_runs,
            "sync_candles": self.sync_candles,
            "preloads_started": self.preloads_started,
            "preloads_completed": self.preloads_completed,
            "invalidations": self.invalidations,
            "uptime_seconds": round(elapsed, 1),
            "ram_hit_rate": round(
                self.ram_hits / max(1, self.ram_hits + self.ram_misses),
                4,
            ),
            "db_hit_rate": round(
                self.db_hits / max(1, self.db_hits + self.db_misses),
                4,
            ),
        }


class MetricsCollector:
    """Mutex-protected metrics store."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._metrics = CacheMetrics()

    def incr(self, name: str, amount: int = 1) -> None:
        with self._lock:
            current = getattr(self._metrics, name, None)
            if isinstance(current, int):
                setattr(self._metrics, name, current + amount)

    def snapshot(self) -> dict[str, float | int]:
        with self._lock:
            return self._metrics.snapshot()

    def reset(self) -> None:
        with self._lock:
            self._metrics = CacheMetrics()
