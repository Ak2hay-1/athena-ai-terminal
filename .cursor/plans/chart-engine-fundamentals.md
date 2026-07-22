# Athena Chart Engine Fundamentals

## Overview

Make Athena Chart deterministic and institutional-grade by fixing candle lifecycle (`TimeBucketEngine` + historical sync + reconnect recovery), then professional axes/crosshair, indicator defaults, viewport/live mode, and automated tests—accuracy first, no new features.

## Root cause of the “giant overnight candle”

Backend returns discrete MT5 bars and does **not** invent multi-hour candles. The frontend creates the bad visual via `applyQuoteToCandle`: after overnight reconnect, a live mid far from the last bar’s close is applied to the **same** candle timestamp, stretching high/low across the entire offline price move while the bar still belongs to the old bucket.

`ChartController.updateLive` only compares timestamp equality/newer—it never validates timeframe bucket boundaries.

**Fix:** ticks must only update the candle whose **UTC bucket** matches the tick time. Crossing a boundary closes the bar and starts a new one (after history sync fills any missing buckets).

## Phase 1 — TimeBucketEngine + sync + reconnect (P0)

### 1.1 New module: `TimeBucketEngine`

Add under `frontend/src/modules/athena-chart/engine/time/`:

| File | Responsibility |
|------|----------------|
| `timeframes.ts` | UTC bucket duration ms for each live TF (`M1`…`D1`) |
| `bucket.ts` | `bucketStartUtc(sec, tf)`, `bucketEndUtc`, `isSameBucket` |
| `TimeBucketEngine.ts` | Stateful forming-candle machine |
| `gapFill.ts` | Insert flat gap candles (OHLC = prev close, vol = 0) between known bars |
| `validateSeries.ts` | Reject / split bars that span >1 bucket |

**`TimeBucketEngine` API (locked):**

```ts
class TimeBucketEngine {
  constructor(tfApi: string) // e.g. "M5"
  reset(history: Candlestick[]): Candlestick[]  // validate + gap-fill
  applyTick(tick: { timeUtcMs: number; mid: number }): {
    series: Candlestick[];
    closed?: Candlestick;
    forming: Candlestick;
  }
  applyServerCandle(c: Candlestick): Candlestick[]
  currentBucketStart(): number
}
```

Rules:
- All bucket math in **UTC**. Local TZ only in formatters.
- New candle only when `bucketStart(tick) > bucketStart(last)`.
- Never merge intervals; never extend H/L of a closed bucket.
- Gap between last history bar and first live tick: prefer **REST backfill** for `[last+1bucket, now]`; if unavailable, insert flat candles up to a **cap** (e.g. 2_000 bars); beyond cap, mark series gap and continue from latest valid—**never** one synthetic giant bar.
- Flat gap candle: `O=H=L=C=prevClose`, `tick_volume=0`, `time` = ISO of bucket open UTC.

### 1.2 Historical synchronization pipeline

Rewrite live data path in `use-live-candles.ts`:

```
connect auth → fetch history → TimeBucketEngine.reset(history)
  → validate timestamps → gap-fill / mark gaps
  → setCandles (render) → subscribe WS → apply ticks via engine only
```

Gate live rendering until first history response settles. Do not call `updateLive` until sync ready.

Expose `loadOlder` + wire `ChartCanvas` `onNeedMoreHistory` (terminal currently missing this).

### 1.3 Reconnection recovery

Extend `use-market-websocket.ts` with `onReconnect` callback.

On reconnect:
1. Pause tick application.
2. Fetch candles from last series timestamp → now.
3. Merge via `mergeCandlesChronological` + gap fill.
4. Resume ticks.

Replace blind `applyQuoteToCandle(last, mid)` with `engine.applyTick(...)`.

### 1.4 Harden `updateLive` / history helpers

- `controller.updateLive`: refuse updates whose bucket ≠ last or next expected.
- `applyLiveCandleUpdate`: same bucket rules.
- Deprecate unrestricted quote stretch for overnight gaps.

## Phase 2 — Indicator defaults (P0, small)

In `types/chart.ts` and `indicator-store.ts`:

```ts
DEFAULT_INDICATORS = {
  ema20: false, ema50: false, /* all false */
  volume: true,
  priceLine: true,
}
instances: []  // no default EMA instances
```

Workspace restore still loads user-saved instances; empty workspace = candles + volume + price line only.

## Phase 3 — Professional axes, crosshair, precision (P1)

### Time axis
- Adaptive local display from UTC epoch: intraday `HH:MM`, multi-day `Jan 12`, monthly `Jan`.
- Tick marks at nice UTC boundaries aligned to TF.

### Price axis
- `formatPriceLabel(price, symbol)` using `priceDigitsFor` (FX 5, JPY 3, metals 2/3).
- Always full instrument precision.

### Crosshair
- Price label on right axis at cursor Y (full precision).
- Time label box under cursor: `18 Jul 2026` / `09:43:00` (TradingView-style).
- OHLC + volume on HUD; ATR/spread placeholders; AI tooltip hook no-op.

### Dynamic price scale
- Smooth padding (~5–8%); lerp target min/max over frames.
- No sudden fit on every tick when in live follow mode.

## Phase 4 — Candles, viewport, navigation, workspace (P1)

- Pixel-align candles; min body 1px; muted opacity for vol=0 gap candles.
- Clip all layers to visible range; memory cap ~100k candles.
- Wire history scroll on terminal; Live mode button; pan left disables live.
- Workspace: restore viewport; never persist candle arrays.

## Phase 5 — Automated tests

Under `frontend/src/modules/athena-chart/engine/time/__tests__/`:
- Bucket boundaries, tick assignment, missing intervals, overnight reconnect
- History sync, time axis format, price precision, timezone construction UTC

## Implementation order

1. TimeBucketEngine + tests
2. Wire sync + reconnect + controller guards
3. Default indicators cleanup
4. Axes / crosshair / precision / price-scale smoothing
5. Candle pixel render + Live mode + history scroll
6. Workspace viewport restore
7. Viewport clip audit + memory cap

## Out of scope

- New AI overlays, indicators, symbols/TFs
- Backend tick→candle aggregation
- Broker session calendars beyond flat gap-fill + history request

## Success criteria

- Overnight reopen: discrete TF bars, never one bar spanning 23:00→08:00
- Fresh chart: candles + volume + price line only
- Crosshair: date+time under cursor; full-precision price on right axis
- Pan left loads history; Live returns to realtime
- Tests green for bucket/reconnect/precision
