import type { Candlestick } from "../../types";
import {
  bucketStartUtcMs,
  isoFromUtcMs,
  timeframeDurationMs,
  utcMsFromIso,
} from "./bucket";

/**
 * Normalize each candle's `time` to its UTC bucket open.
 * Does not invent OHLC — only snaps timestamps to valid bucket starts.
 */
export function snapToBucketOpens(
  candles: Candlestick[],
  tf: string,
): Candlestick[] {
  return candles.map((c) => {
    const start = bucketStartUtcMs(utcMsFromIso(c.time), tf);
    return { ...c, time: isoFromUtcMs(start), timeframe: tf.toUpperCase() };
  });
}

/**
 * Drop bars whose open time is not aligned to a bucket boundary
 * (after snap, all should be aligned — this catches corrupt spans).
 * A bar is invalid if its recorded time falls more than half a bucket
 * off the floor (already snapped away) — kept for API clarity.
 */
export function validateSeries(
  candles: Candlestick[],
  tf: string,
): Candlestick[] {
  const dur = timeframeDurationMs(tf);
  if (dur == null) return candles;

  const snapped = snapToBucketOpens(candles, tf);
  const byBucket = new Map<number, Candlestick>();

  for (const c of snapped) {
    const start = bucketStartUtcMs(utcMsFromIso(c.time), tf);
    const existing = byBucket.get(start);
    // Prefer the later-received / higher-volume bar for the same bucket
    if (
      !existing ||
      c.tick_volume >= existing.tick_volume ||
      utcMsFromIso(c.time) >= utcMsFromIso(existing.time)
    ) {
      byBucket.set(start, { ...c, time: isoFromUtcMs(start) });
    }
  }

  return Array.from(byBucket.entries())
    .sort((a, b) => a[0] - b[0])
    .map(([, c]) => c);
}

/** True if high-low range looks like a multi-session stretch (heuristic guard). */
export function looksLikeGiantBar(
  candle: Candlestick,
  typicalRange: number,
): boolean {
  if (typicalRange <= 0) return false;
  const range = candle.high - candle.low;
  return range > typicalRange * 20;
}
