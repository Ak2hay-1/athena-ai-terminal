"""
Background preloader.

When a user opens EURUSD M5, silently warm:

    EURUSD M1, M15, H1, H4

Also preloads watchlist symbols and recently viewed symbols.

Priority: open chart → watchlist → recently viewed.
Never blocks the request path; work runs on a bounded thread pool.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable

from app.cache.logging_utils import cache_log


@dataclass(order=True)
class _PreloadJob:
    priority: int
    symbol: str
    timeframe: str
    limit: int


class BackgroundPreloader:
    """
    Deduped, priority-ordered background warmer for CacheManager.
    """

    PRIORITY_OPEN = 0
    PRIORITY_RELATED = 1
    PRIORITY_WATCHLIST = 2
    PRIORITY_RECENT = 3

    def __init__(
        self,
        *,
        warm_fn: Callable[[str, str, int], None],
        enabled: bool = True,
        workers: int = 2,
        default_limit: int = 500,
        related_timeframes: list[str] | None = None,
    ) -> None:
        self._warm_fn = warm_fn
        self.enabled = enabled
        self.default_limit = max(50, int(default_limit))
        self.related_timeframes = [
            tf.upper() for tf in (related_timeframes or ["M1", "M15", "H1", "H4"])
        ]

        self._lock = threading.Lock()
        self._pending: set[tuple[str, str]] = set()
        self._recent: deque[str] = deque(maxlen=32)
        self._watchlist: list[str] = []
        self._executor: ThreadPoolExecutor | None = None
        self._workers = max(1, int(workers))
        self._started = False

    def start(self) -> None:
        if not self.enabled or self._started:
            return
        self._executor = ThreadPoolExecutor(
            max_workers=self._workers,
            thread_name_prefix="athena-cache-preload",
        )
        self._started = True

    def stop(self) -> None:
        executor = self._executor
        self._executor = None
        self._started = False
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)

    def set_watchlist(self, symbols: list[str]) -> None:
        with self._lock:
            self._watchlist = [s.upper() for s in symbols if s]

    def note_recent(self, symbol: str) -> None:
        symbol = symbol.upper()
        with self._lock:
            if symbol in self._recent:
                self._recent.remove(symbol)
            self._recent.appendleft(symbol)

    def on_chart_open(
        self,
        symbol: str,
        timeframe: str,
        *,
        limit: int | None = None,
    ) -> None:
        """Warm the open chart series, then related TFs / watchlist / recent."""

        if not self.enabled or not self._started:
            return

        symbol = symbol.upper()
        timeframe = timeframe.upper()
        limit = limit or self.default_limit

        self.note_recent(symbol)
        self._enqueue(self.PRIORITY_OPEN, symbol, timeframe, limit)

        for related in self.related_timeframes:
            if related == timeframe:
                continue
            self._enqueue(self.PRIORITY_RELATED, symbol, related, limit)

        with self._lock:
            watchlist = list(self._watchlist)
            recent = list(self._recent)

        for sym in watchlist:
            if sym == symbol:
                continue
            self._enqueue(
                self.PRIORITY_WATCHLIST,
                sym,
                timeframe,
                limit,
            )

        for sym in recent:
            if sym == symbol or sym in watchlist:
                continue
            self._enqueue(self.PRIORITY_RECENT, sym, timeframe, limit)

    def preload(
        self,
        symbol: str,
        timeframe: str,
        *,
        priority: int = PRIORITY_RELATED,
        limit: int | None = None,
    ) -> None:
        self._enqueue(
            priority,
            symbol.upper(),
            timeframe.upper(),
            limit or self.default_limit,
        )

    # ------------------------------------------------------------------

    def _enqueue(
        self,
        priority: int,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> None:
        if not self.enabled or not self._started or self._executor is None:
            return

        key = (symbol, timeframe)
        with self._lock:
            if key in self._pending:
                return
            self._pending.add(key)

        job = _PreloadJob(
            priority=priority,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        self._executor.submit(self._run_job, job)

    def _run_job(self, job: _PreloadJob) -> None:
        key = (job.symbol, job.timeframe)
        cache_log(
            "PRELOAD START",
            symbol=job.symbol,
            timeframe=job.timeframe,
            priority=job.priority,
            limit=job.limit,
        )
        started = time.perf_counter()
        try:
            self._warm_fn(job.symbol, job.timeframe, job.limit)
            cache_log(
                "PRELOAD COMPLETE",
                symbol=job.symbol,
                timeframe=job.timeframe,
                ms=round((time.perf_counter() - started) * 1000, 1),
            )
        except Exception:
            from app.core.logger import get_logger

            get_logger("athena.cache").exception(
                "Preload failed for %s %s",
                job.symbol,
                job.timeframe,
            )
        finally:
            with self._lock:
                self._pending.discard(key)
