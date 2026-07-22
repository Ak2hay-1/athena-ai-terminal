"""
Standalone MT5 reachability probe, run in a throwaway subprocess.

``mt5.initialize()`` is a blocking native call that can hang forever (and,
empirically, does not release the GIL while blocked) when the MT5 terminal
isn't installed/running/reachable. A thread-based timeout cannot recover
from that — only killing the whole OS process can. This module is kept
import-light (MetaTrader5 + stdlib only) so the probe subprocess starts
fast and never drags in the rest of the application.
"""

from __future__ import annotations

from multiprocessing import Queue


def probe_initialize(
    path: str,
    login: int,
    password: str,
    server: str,
    result_queue: "Queue[bool]",
) -> None:
    try:
        import MetaTrader5 as mt5
    except ImportError:
        result_queue.put(False)
        return

    try:
        ok = mt5.initialize(
            path=path,
            login=login,
            password=password,
            server=server,
        )
        result_queue.put(bool(ok))
        if ok:
            mt5.shutdown()
    except Exception:
        result_queue.put(False)
