/**
 * Background preload helpers for related timeframes / watchlist.
 * Fire-and-forget — never blocks chart paint.
 */

import {
  PRELOAD_TIMEFRAMES,
  getCachedSeries,
  putCachedSeries,
} from "@/lib/candle-series-cache";
import { apiFetch } from "@/services/api-client";
import { getCandles } from "@/services/market";

const inflight = new Set<string>();

function key(symbol: string, timeframe: string): string {
  return `${symbol.toUpperCase()}:${timeframe.toUpperCase()}`;
}

/**
 * Warm related timeframes for the open chart symbol.
 * Skips the active timeframe and any series already in the client cache.
 */
export function preloadRelatedTimeframes(
  symbol: string,
  activeTimeframe: string,
  limit = 500,
): void {
  if (!symbol) return;
  const active = activeTimeframe.toUpperCase();
  for (const tf of PRELOAD_TIMEFRAMES) {
    if (tf === active) continue;
    void warmSeries(symbol, tf, limit);
  }
}

export function preloadWatchlist(
  symbols: string[],
  timeframe: string,
  limit = 500,
): void {
  for (const symbol of symbols) {
    void warmSeries(symbol, timeframe, limit);
  }
}

async function warmSeries(
  symbol: string,
  timeframe: string,
  limit: number,
): Promise<void> {
  const k = key(symbol, timeframe);
  if (inflight.has(k)) return;
  if (getCachedSeries(symbol, timeframe)) return;

  inflight.add(k);
  try {
    // Hint backend CacheManager to warm RAM/DB (best-effort).
    void apiFetch(
      `/market/cache/preload?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`,
      { method: "POST" },
    ).catch(() => undefined);

    const batch = await getCandles(symbol, timeframe, limit);
    if (batch.length) {
      putCachedSeries(symbol, timeframe, batch);
    }
  } catch {
    // Preload is best-effort.
  } finally {
    inflight.delete(k);
  }
}
