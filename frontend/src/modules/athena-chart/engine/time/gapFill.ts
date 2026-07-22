import type { Candlestick } from "../../types";
import {
  MAX_GAP_FILL_BARS,
  bucketStartUtcMs,
  isoFromUtcMs,
  nextBucketStartUtcMs,
  utcMsFromIso,
} from "./bucket";

export interface GapFillResult {
  candles: Candlestick[];
  /** True when gap exceeded MAX_GAP_FILL_BARS and was not fully filled. */
  truncated: boolean;
  /** ISO time where continuous data resumes after a truncated gap. */
  dataGapFrom: string | null;
}

function flatCandle(
  template: Pick<Candlestick, "symbol" | "timeframe">,
  bucketStartMs: number,
  prevClose: number,
): Candlestick {
  return {
    symbol: template.symbol,
    timeframe: template.timeframe,
    time: isoFromUtcMs(bucketStartMs),
    open: prevClose,
    high: prevClose,
    low: prevClose,
    close: prevClose,
    tick_volume: 0,
  };
}

/**
 * Insert flat candles (O=H=L=C=prevClose, vol=0) for every missing bucket
 * between consecutive bars. Caps fill at MAX_GAP_FILL_BARS per gap.
 */
export function fillMissingBuckets(
  candles: Candlestick[],
  tf: string,
  maxFill: number = MAX_GAP_FILL_BARS,
): GapFillResult {
  if (candles.length === 0) {
    return { candles: [], truncated: false, dataGapFrom: null };
  }

  const out: Candlestick[] = [];
  let truncated = false;
  let dataGapFrom: string | null = null;

  for (let i = 0; i < candles.length; i++) {
    const cur = candles[i];
    if (i === 0) {
      out.push(cur);
      continue;
    }

    const prev = out[out.length - 1];
    const prevStart = bucketStartUtcMs(utcMsFromIso(prev.time), tf);
    const curStart = bucketStartUtcMs(utcMsFromIso(cur.time), tf);

    if (curStart <= prevStart) {
      // Same or older bucket — keep latest (caller should have deduped)
      out[out.length - 1] = cur;
      continue;
    }

    let cursor = nextBucketStartUtcMs(prevStart, tf);
    let filled = 0;
    let prevClose = prev.close;

    while (cursor < curStart) {
      if (filled >= maxFill) {
        truncated = true;
        dataGapFrom = isoFromUtcMs(cursor);
        // Jump to current bar without filling the rest
        break;
      }
      out.push(flatCandle(cur, cursor, prevClose));
      filled += 1;
      cursor = nextBucketStartUtcMs(cursor, tf);
    }

    out.push(cur);
  }

  return { candles: out, truncated, dataGapFrom };
}

/**
 * Fill buckets from after `last` up to (but not including) `untilBucketStartMs`.
 */
export function fillForwardTo(
  last: Candlestick,
  untilBucketStartMs: number,
  tf: string,
  maxFill: number = MAX_GAP_FILL_BARS,
): { candles: Candlestick[]; truncated: boolean } {
  const out: Candlestick[] = [];
  let cursor = nextBucketStartUtcMs(
    bucketStartUtcMs(utcMsFromIso(last.time), tf),
    tf,
  );
  let filled = 0;
  let prevClose = last.close;
  let truncated = false;

  while (cursor < untilBucketStartMs) {
    if (filled >= maxFill) {
      truncated = true;
      break;
    }
    out.push(flatCandle(last, cursor, prevClose));
    filled += 1;
    cursor = nextBucketStartUtcMs(cursor, tf);
  }

  return { candles: out, truncated };
}
