"""
Athena multi-layer market cache.

All historical candle, indicator, and short-lived AI-context access should
go through ``CacheManager``. Live account state (bid/ask for trading,
positions, orders, margin, balance, equity) is intentionally excluded —
those always come directly from MT5.

Layers:
    1. RAM  – LRU series cache for active charts (ultra-fast)
    2. DB   – PostgreSQL historical candles / indicator values
    3. MT5  – source of truth; gap-only sync of missing completed bars
"""

from app.cache.manager import CacheManager
from app.cache.manager import cache_manager

__all__ = [
    "CacheManager",
    "cache_manager",
]
