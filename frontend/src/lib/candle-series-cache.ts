/**
 * Client-side candle series cache (Layer 1 mirror).
 *
 * Serves instant chart reopen / timeframe switches without waiting on
 * the network. Complements the backend CacheManager — never stores
 * account state. Forming live candles are applied by the live hook;
 * this store holds completed history batches only.
 */

import type { Candle } from "@/types";

export type SeriesKey = string;

type Entry = {
  candles: Candle[];
  updatedAt: number;
};

const DEFAULT_MAX_SERIES = 48;
const DEFAULT_MAX_CANDLES = 5000;

const store = new Map<SeriesKey, Entry>();
const lru: SeriesKey[] = [];

let maxSeries = DEFAULT_MAX_SERIES;
let maxCandles = DEFAULT_MAX_CANDLES;

/** Related timeframes preloaded when a chart opens. */
export const PRELOAD_TIMEFRAMES = ["M1", "M15", "H1", "H4"] as const;

export function seriesKey(symbol: string, timeframe: string): SeriesKey {
  return `${symbol.toUpperCase()}:${timeframe.toUpperCase()}`;
}

export function configureCandleSeriesCache(opts: {
  maxSeries?: number;
  maxCandles?: number;
}): void {
  if (opts.maxSeries != null) maxSeries = Math.max(4, opts.maxSeries);
  if (opts.maxCandles != null) maxCandles = Math.max(100, opts.maxCandles);
}

function touch(key: SeriesKey): void {
  const idx = lru.indexOf(key);
  if (idx >= 0) lru.splice(idx, 1);
  lru.push(key);
  while (lru.length > maxSeries) {
    const evict = lru.shift();
    if (evict) store.delete(evict);
  }
}

function trim(candles: Candle[]): Candle[] {
  if (candles.length <= maxCandles) return candles;
  return candles.slice(candles.length - maxCandles);
}

export function getCachedSeries(
  symbol: string,
  timeframe: string,
): Candle[] | null {
  const key = seriesKey(symbol, timeframe);
  const entry = store.get(key);
  if (!entry || entry.candles.length === 0) return null;
  touch(key);
  if (typeof console !== "undefined" && process.env.NODE_ENV !== "production") {
    // eslint-disable-next-line no-console
    console.debug("[CACHE] RAM HIT", key, entry.candles.length);
  }
  return entry.candles.map((c) => ({ ...c }));
}

export function putCachedSeries(
  symbol: string,
  timeframe: string,
  candles: Candle[],
): void {
  if (!candles.length) return;
  const key = seriesKey(symbol, timeframe);
  store.set(key, {
    candles: trim(candles.map((c) => ({ ...c }))),
    updatedAt: Date.now(),
  });
  touch(key);
}

export function appendCachedCandle(
  symbol: string,
  timeframe: string,
  candle: Candle,
): void {
  const key = seriesKey(symbol, timeframe);
  const entry = store.get(key);
  if (!entry) {
    putCachedSeries(symbol, timeframe, [candle]);
    return;
  }
  const last = entry.candles[entry.candles.length - 1];
  if (last && last.time === candle.time) {
    entry.candles[entry.candles.length - 1] = { ...candle };
  } else {
    entry.candles.push({ ...candle });
    entry.candles = trim(entry.candles);
  }
  entry.updatedAt = Date.now();
  touch(key);
}

export function invalidateCachedSeries(
  symbol?: string,
  timeframe?: string,
): void {
  if (!symbol && !timeframe) {
    store.clear();
    lru.length = 0;
    return;
  }
  const sym = symbol?.toUpperCase();
  const tf = timeframe?.toUpperCase();
  for (const key of [...store.keys()]) {
    const [s, t] = key.split(":");
    if (sym && s !== sym) continue;
    if (tf && t !== tf) continue;
    store.delete(key);
    const idx = lru.indexOf(key);
    if (idx >= 0) lru.splice(idx, 1);
  }
}

export function candleSeriesCacheStats(): {
  series: number;
  candles: number;
} {
  let candles = 0;
  for (const entry of store.values()) candles += entry.candles.length;
  return { series: store.size, candles };
}
