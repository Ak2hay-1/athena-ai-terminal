import type { Candlestick } from "../../types";
import {
  bucketStartUtcMs,
  isoFromUtcMs,
  nextBucketStartUtcMs,
  timeframeDurationMs,
  utcMsFromIso,
} from "./bucket";
import { fillForwardTo, fillMissingBuckets } from "./gapFill";
import { validateSeries } from "./validateSeries";

export type SyncStatus = "idle" | "loading" | "ready" | "degraded";

export interface ApplyTickResult {
  series: Candlestick[];
  closed?: Candlestick;
  forming: Candlestick;
  /** True when forward gap fill was truncated. */
  truncated?: boolean;
}

/**
 * Deterministic candle lifecycle: ticks map only to UTC timeframe buckets.
 * Never merges multiple intervals into one candle.
 */
export class TimeBucketEngine {
  readonly tf: string;
  private symbol = "";
  private series: Candlestick[] = [];
  private dataGapFrom: string | null = null;

  constructor(tfApi: string) {
    const upper = tfApi.toUpperCase();
    if (timeframeDurationMs(upper) == null) {
      throw new Error(`TimeBucketEngine: unsupported timeframe ${tfApi}`);
    }
    this.tf = upper;
  }

  getSeries(): Candlestick[] {
    return this.series;
  }

  getDataGapFrom(): string | null {
    return this.dataGapFrom;
  }

  currentBucketStart(): number | null {
    const last = this.series[this.series.length - 1];
    if (!last) return null;
    return bucketStartUtcMs(utcMsFromIso(last.time), this.tf);
  }

  /**
   * Replace series with validated history.
   * Only fills tiny holes (1–3 missing buckets). Large gaps (overnight/weekend)
   * are left as time jumps — never expanded into thousands of flats (that freezes the UI).
   */
  reset(history: Candlestick[]): Candlestick[] {
    if (history.length > 0) {
      this.symbol = history[0].symbol;
    }
    const validated = validateSeries(history, this.tf);
    // maxFill=3: patch single-bar holes only; skip session/weekend spans
    const filled = fillMissingBuckets(validated, this.tf, 3);
    this.series = filled.candles;
    // Don't mark degraded for skipped weekend gaps — those are expected
    this.dataGapFrom = null;
    return this.series;
  }

  /**
   * Merge a server candle (closed or forming) into the series by bucket.
   */
  applyServerCandle(c: Candlestick): Candlestick[] {
    if (!this.symbol) this.symbol = c.symbol;
    const start = bucketStartUtcMs(utcMsFromIso(c.time), this.tf);
    const snapped: Candlestick = {
      ...c,
      symbol: c.symbol || this.symbol,
      timeframe: this.tf,
      time: isoFromUtcMs(start),
    };

    if (this.series.length === 0) {
      this.series = [snapped];
      return this.series;
    }

    const last = this.series[this.series.length - 1];
    const lastStart = bucketStartUtcMs(utcMsFromIso(last.time), this.tf);

    if (start === lastStart) {
      const next = [...this.series];
      next[next.length - 1] = snapped;
      this.series = next;
      return this.series;
    }

    if (start < lastStart) {
      // Out-of-order / older — merge into history by bucket
      const validated = validateSeries([...this.series, snapped], this.tf);
      const filled = fillMissingBuckets(validated, this.tf);
      this.series = filled.candles;
      if (filled.dataGapFrom) this.dataGapFrom = filled.dataGapFrom;
      return this.series;
    }

    // Future bucket — fill small gaps then append
    const { candles: gaps, truncated } = fillForwardTo(last, start, this.tf, 120);
    if (truncated) {
      this.dataGapFrom = isoFromUtcMs(nextBucketStartUtcMs(lastStart, this.tf));
    }
    this.series = [...this.series, ...gaps, snapped];
    return this.series;
  }

  /**
   * Apply a live tick mid. Only updates the candle for the tick's UTC bucket.
   * Crossing a boundary closes the prior bar and opens a new forming candle.
   * Never stretches an old overnight bar with a gapped mid.
   */
  applyTick(tick: {
    timeUtcMs: number;
    mid: number;
    symbol?: string;
  }): ApplyTickResult {
    const mid = tick.mid;
    if (!Number.isFinite(mid) || mid <= 0) {
      const last = this.series[this.series.length - 1];
      return {
        series: this.series,
        forming: last ?? this.emptyForming(tick.timeUtcMs, mid || 0),
      };
    }

    if (tick.symbol) this.symbol = tick.symbol.toUpperCase();
    const tickBucket = bucketStartUtcMs(tick.timeUtcMs, this.tf);

    if (this.series.length === 0) {
      const forming = this.newForming(tickBucket, mid);
      this.series = [forming];
      return { series: this.series, forming };
    }

    const last = this.series[this.series.length - 1];
    const lastBucket = bucketStartUtcMs(utcMsFromIso(last.time), this.tf);

    // Tick belongs to current forming bucket — update OHLC in place
    if (tickBucket === lastBucket) {
      const forming: Candlestick = {
        ...last,
        high: Math.max(last.high, mid),
        low: Math.min(last.low, mid),
        close: mid,
        tick_volume: last.tick_volume + 1,
      };
      const next = [...this.series];
      next[next.length - 1] = forming;
      this.series = next;
      return { series: this.series, forming };
    }

    // Tick is in the past relative to last bar — ignore (stale)
    if (tickBucket < lastBucket) {
      return { series: this.series, forming: last };
    }

    // Tick is in a future bucket — close last (unchanged), fill small gaps, open new
    const closed = last;
    // Cap forward fill: short disconnects only. Long gaps → REST resync should have run.
    const { candles: gaps, truncated } = fillForwardTo(
      last,
      tickBucket,
      this.tf,
      120,
    );
    if (truncated) {
      this.dataGapFrom = isoFromUtcMs(
        nextBucketStartUtcMs(lastBucket, this.tf),
      );
    }

    const prevClose =
      gaps.length > 0 ? gaps[gaps.length - 1].close : last.close;
    // If truncated, jump straight to tick bucket (no mega-bar, no 2k flats)
    const forming = this.newForming(tickBucket, mid, prevClose);
    this.series = [...this.series, ...gaps, forming];
    return {
      series: this.series,
      closed,
      forming,
      truncated,
    };
  }

  private newForming(
    bucketStartMs: number,
    mid: number,
    open?: number,
  ): Candlestick {
    const o = open ?? mid;
    return {
      symbol: this.symbol || "UNKNOWN",
      timeframe: this.tf,
      time: isoFromUtcMs(bucketStartMs),
      open: o,
      high: Math.max(o, mid),
      low: Math.min(o, mid),
      close: mid,
      tick_volume: 1,
    };
  }

  private emptyForming(timeUtcMs: number, mid: number): Candlestick {
    const start = bucketStartUtcMs(timeUtcMs, this.tf);
    return this.newForming(start, mid || 0);
  }
}
