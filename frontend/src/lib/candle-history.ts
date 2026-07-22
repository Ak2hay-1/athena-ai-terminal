import type { Candle } from "@/types";
import {
  bucketStartUtcMs,
  isoFromUtcMs,
  utcMsFromIso,
} from "@/modules/athena-chart/engine/time";

/** Initial chart load size — keep modest so first paint is fast. */
export const INITIAL_CANDLE_LIMIT = 500;

/** Batch size when scrolling into older history. */
export const HISTORY_BATCH_SIZE = 500;

/**
 * How many bars from the left edge of the visible logical range
 * trigger an older-history request.
 */
export const HISTORY_VISIBLE_THRESHOLD = 80;

/** Soft cap for in-memory series (drop oldest when exceeded). */
export const MAX_SERIES_CANDLES = 100_000;

/** Merge older + newer candles: unique by timestamp, ascending time. */
export function mergeCandlesChronological(
  existing: Candle[],
  incoming: Candle[],
): Candle[] {
  if (incoming.length === 0) return existing;
  if (existing.length === 0) return sortCandlesAscending(dedupeByTime(incoming));

  const byTime = new Map<string, Candle>();
  for (const candle of existing) {
    byTime.set(candle.time, candle);
  }
  for (const candle of incoming) {
    byTime.set(candle.time, candle);
  }

  return Array.from(byTime.values()).sort(
    (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime(),
  );
}

export function dedupeByTime(candles: Candle[]): Candle[] {
  const byTime = new Map<string, Candle>();
  for (const candle of candles) {
    byTime.set(candle.time, candle);
  }
  return Array.from(byTime.values());
}

export function sortCandlesAscending(candles: Candle[]): Candle[] {
  return [...candles].sort(
    (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime(),
  );
}

export function trimSeriesToCap<T>(candles: T[], max = MAX_SERIES_CANDLES): T[] {
  if (candles.length <= max) return candles;
  return candles.slice(candles.length - max);
}

/**
 * Apply a live candle update using UTC timeframe buckets.
 * Same bucket → replace. Older → merge. Newer → append (caller should gap-fill).
 * Never stretches an old bar when timestamps differ across buckets.
 */
export function applyLiveCandleUpdate(
  current: Candle[] | undefined,
  mapped: Candle,
): Candle[] {
  if (!current || current.length === 0) return [mapped];

  const tf = (mapped.timeframe || current[0]?.timeframe || "M5").toUpperCase();
  let mappedStart: number;
  let lastStart: number;
  try {
    mappedStart = bucketStartUtcMs(utcMsFromIso(mapped.time), tf);
    lastStart = bucketStartUtcMs(utcMsFromIso(current[current.length - 1].time), tf);
  } catch {
    // Fallback to exact ISO equality if TF unknown
    const next = [...current];
    const last = next[next.length - 1];
    if (last && last.time === mapped.time) {
      next[next.length - 1] = mapped;
      return next;
    }
    if (last && new Date(mapped.time).getTime() < new Date(last.time).getTime()) {
      return mergeCandlesChronological(next, [mapped]);
    }
    next.push(mapped);
    return next;
  }

  const snapped: Candle = {
    ...mapped,
    time: isoFromUtcMs(mappedStart),
    timeframe: tf,
  };

  if (mappedStart === lastStart) {
    const next = [...current];
    next[next.length - 1] = snapped;
    return next;
  }

  if (mappedStart < lastStart) {
    return mergeCandlesChronological(current, [snapped]);
  }

  return [...current, snapped];
}
