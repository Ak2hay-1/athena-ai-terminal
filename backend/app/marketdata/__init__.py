"""
Athena Market Data Engine.

Professional tick-to-candle pipeline:

    MT5 (live ticks only)
        -> TickCollector
        -> CandleEngine (time-based OHLC buckets)
        -> PersistenceWriter (PostgreSQL)  +  LiveMarketCache (Redis)
        -> CacheManager (RAM series + indicator / AI context)
        -> IndicatorUpdater / AnalysisDispatcher / WebSocket broadcasts

Historical chart reads go through CacheManager:

    RAM (LRU) -> local database -> MT5 gap-only sync

The local database is the primary source of historical market data.
MT5 is used only for live ticks, the initial history download, and
filling gaps after downtime. Forming candles are never stored as
immutable history. Account state is never cached.
"""
