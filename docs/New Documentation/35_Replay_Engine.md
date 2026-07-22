# Institutional Replay Engine

Interactive historical market simulator. **Not** a strategy tester.

Athena runs the **same production pipeline** used for live trading, using only candles available at the replay cursor.

## Pipeline

```text
Historical Candles (sliced to current_index)
        ↓
Indicator Engine
        ↓
SMC Engine
        ↓
Multi-Timeframe Analysis (HTF truncated to as_of)
        ↓
Risk Engine
        ↓
Recommendation Engine (persist=False)
        ↓
Institutional + Probability enrichments
        ↓
Redis session + WebSocket candle_update
```

## Time-travel protection

At cursor time `T`:

- Primary frame = `df.iloc[:current_index+1]`
- HTF frames filtered with `time <= T`
- Never call `MarketService.analyze_latest` (loads wall-clock latest)

Warmup bars before `start` are loaded for indicator stability but the UI timeline begins at `start`.

## Storage

| Data | Store |
|------|--------|
| Session, timeline, trades, stats | Redis `athena:replay:{session_id}` |
| Candle OHLCV | PostgreSQL `market_candles` |
| Process DataFrame cache | In-memory `ReplayCandleCache` |

If Redis is unavailable, `POST /replay/start` returns **503**.

## APIs

| Method | Path |
|--------|------|
| POST | `/api/v1/replay/start` |
| GET | `/api/v1/replay/{session_id}` |
| POST | `/api/v1/replay/{session_id}/next` |
| POST | `/api/v1/replay/{session_id}/previous` |
| POST | `/api/v1/replay/{session_id}/jump` |
| POST | `/api/v1/replay/{session_id}/pause` |
| POST | `/api/v1/replay/{session_id}/resume` |
| POST | `/api/v1/replay/{session_id}/speed` |
| POST | `/api/v1/replay/{session_id}/reset` |
| POST | `/api/v1/replay/{session_id}/accept-trade` |
| GET | `/api/v1/replay/{session_id}/report` |
| DELETE | `/api/v1/replay/{session_id}` |

## WebSocket

Each step broadcasts the same `candle_update` payload as live mode via `broadcast_candle_update`. The `/replay` page subscribes with `useMarketWebSocket` and does **not** poll live quotes.

## Speeds

`1x` = 1000ms per candle (configurable `REPLAY_BASE_TICK_MS`), then `2x`, `5x`, `10x`, `25x`, `100x`.

## Frontend

Route: `/replay` — controls, chart, recommendation panel, timeline, statistics, trade history.

## Distinction from BacktestEngine

`app/backtesting/backtest_engine.py` is an offline batch runner. Replay is interactive, Redis-backed, WS-driven, and never writes recommendations into the live learning store (`persist=False`).
