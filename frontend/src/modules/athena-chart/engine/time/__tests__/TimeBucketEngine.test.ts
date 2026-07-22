import { describe, expect, it } from "vitest";
import {
  TimeBucketEngine,
  bucketStartUtcMs,
  fillMissingBuckets,
  isSameBucket,
  isoFromUtcMs,
  validateSeries,
} from "../index";
import type { Candlestick } from "../../../types";

function bar(
  partial: Partial<Candlestick> & { time: string; close: number },
): Candlestick {
  const c = partial.close;
  return {
    symbol: "EURUSD",
    timeframe: "M5",
    open: partial.open ?? c,
    high: partial.high ?? c,
    low: partial.low ?? c,
    tick_volume: partial.tick_volume ?? 10,
    ...partial,
  };
}

describe("bucketStartUtcMs", () => {
  it("aligns M1 to minute boundaries", () => {
    const t = Date.UTC(2026, 6, 21, 10, 0, 45);
    expect(bucketStartUtcMs(t, "M1")).toBe(Date.UTC(2026, 6, 21, 10, 0, 0));
  });

  it("aligns M5 to 5-minute boundaries", () => {
    const t = Date.UTC(2026, 6, 21, 10, 7, 30);
    expect(bucketStartUtcMs(t, "M5")).toBe(Date.UTC(2026, 6, 21, 10, 5, 0));
  });

  it("aligns D1 to UTC midnight", () => {
    const t = Date.UTC(2026, 6, 21, 15, 30, 0);
    expect(bucketStartUtcMs(t, "D1")).toBe(Date.UTC(2026, 6, 21, 0, 0, 0));
  });

  it("isSameBucket within M1 minute", () => {
    const a = Date.UTC(2026, 6, 21, 10, 0, 10);
    const b = Date.UTC(2026, 6, 21, 10, 0, 59);
    expect(isSameBucket(a, b, "M1")).toBe(true);
    expect(isSameBucket(a, Date.UTC(2026, 6, 21, 10, 1, 0), "M1")).toBe(false);
  });
});

describe("fillMissingBuckets", () => {
  it("inserts flat candles for missing M5 intervals", () => {
    const a = bar({
      time: isoFromUtcMs(Date.UTC(2026, 6, 21, 10, 0, 0)),
      close: 1.1,
    });
    const b = bar({
      time: isoFromUtcMs(Date.UTC(2026, 6, 21, 10, 15, 0)),
      close: 1.2,
    });
    const { candles, truncated } = fillMissingBuckets([a, b], "M5");
    expect(truncated).toBe(false);
    // 10:00, 10:05, 10:10, 10:15
    expect(candles).toHaveLength(4);
    expect(candles[1].tick_volume).toBe(0);
    expect(candles[1].open).toBe(1.1);
    expect(candles[1].close).toBe(1.1);
    expect(candles[2].time).toBe(isoFromUtcMs(Date.UTC(2026, 6, 21, 10, 10, 0)));
  });

  it("never creates one giant merged candle across a gap", () => {
    const a = bar({
      time: isoFromUtcMs(Date.UTC(2026, 6, 20, 23, 0, 0)),
      close: 2650,
      high: 2651,
      low: 2649,
      open: 2650,
      symbol: "XAUUSD",
      timeframe: "M5",
    });
    const b = bar({
      time: isoFromUtcMs(Date.UTC(2026, 6, 21, 8, 0, 0)),
      close: 2680,
      high: 2681,
      low: 2679,
      open: 2680,
      symbol: "XAUUSD",
      timeframe: "M5",
    });
    const { candles } = fillMissingBuckets([a, b], "M5");
    expect(candles.length).toBeGreaterThan(2);
    // No single bar spans 23:00 open with 08:00 close range
    for (const c of candles) {
      expect(c.high - c.low).toBeLessThan(5);
    }
  });
});

describe("TimeBucketEngine", () => {
  it("keeps tick at :59 in current M1 bucket", () => {
    const engine = new TimeBucketEngine("M1");
    const open = Date.UTC(2026, 6, 21, 10, 0, 0);
    engine.reset([
      bar({
        time: isoFromUtcMs(open),
        close: 1.1,
        open: 1.1,
        high: 1.1,
        low: 1.1,
        timeframe: "M1",
      }),
    ]);
    const r = engine.applyTick({
      timeUtcMs: Date.UTC(2026, 6, 21, 10, 0, 59),
      mid: 1.105,
    });
    expect(r.series).toHaveLength(1);
    expect(r.forming.close).toBe(1.105);
    expect(r.forming.high).toBe(1.105);
    expect(r.closed).toBeUndefined();
  });

  it("opens a new candle at the next minute boundary", () => {
    const engine = new TimeBucketEngine("M1");
    const open = Date.UTC(2026, 6, 21, 10, 0, 0);
    engine.reset([
      bar({
        time: isoFromUtcMs(open),
        close: 1.1,
        timeframe: "M1",
      }),
    ]);
    const r = engine.applyTick({
      timeUtcMs: Date.UTC(2026, 6, 21, 10, 1, 0),
      mid: 1.12,
    });
    expect(r.series).toHaveLength(2);
    expect(r.closed?.time).toBe(isoFromUtcMs(open));
    expect(r.forming.time).toBe(
      isoFromUtcMs(Date.UTC(2026, 6, 21, 10, 1, 0)),
    );
    expect(r.forming.open).toBe(1.1); // prev close
    expect(r.forming.close).toBe(1.12);
  });

  it("does not stretch overnight bar when mid gaps after reconnect", () => {
    const engine = new TimeBucketEngine("M5");
    const evening = Date.UTC(2026, 6, 20, 23, 0, 0);
    engine.reset([
      bar({
        symbol: "XAUUSD",
        timeframe: "M5",
        time: isoFromUtcMs(evening),
        open: 2650,
        high: 2651,
        low: 2649,
        close: 2650,
      }),
    ]);

    // Morning tick — new buckets, not stretch of 23:00 bar
    const r = engine.applyTick({
      timeUtcMs: Date.UTC(2026, 6, 21, 8, 0, 15),
      mid: 2680,
      symbol: "XAUUSD",
    });

    const first = r.series[0];
    expect(first.high).toBe(2651);
    expect(first.low).toBe(2649);
    expect(first.close).toBe(2650);
    expect(r.forming.close).toBe(2680);
    expect(r.forming.time).toBe(
      isoFromUtcMs(Date.UTC(2026, 6, 21, 8, 0, 0)),
    );
    expect(r.series.length).toBeGreaterThan(1);
  });

  it("applyServerCandle replaces same bucket", () => {
    const engine = new TimeBucketEngine("M5");
    const t = isoFromUtcMs(Date.UTC(2026, 6, 21, 10, 5, 0));
    engine.reset([bar({ time: t, close: 1.1, timeframe: "M5" })]);
    engine.applyServerCandle(
      bar({ time: t, close: 1.15, high: 1.16, low: 1.09, timeframe: "M5" }),
    );
    expect(engine.getSeries()).toHaveLength(1);
    expect(engine.getSeries()[0].close).toBe(1.15);
  });
});

describe("validateSeries", () => {
  it("dedupes same bucket keeping one bar", () => {
    const t = isoFromUtcMs(Date.UTC(2026, 6, 21, 10, 5, 30));
    const a = bar({ time: t, close: 1.1, tick_volume: 5, timeframe: "M5" });
    const b = bar({
      time: isoFromUtcMs(Date.UTC(2026, 6, 21, 10, 5, 50)),
      close: 1.12,
      tick_volume: 20,
      timeframe: "M5",
    });
    const out = validateSeries([a, b], "M5");
    expect(out).toHaveLength(1);
    expect(out[0].close).toBe(1.12);
    expect(out[0].time).toBe(isoFromUtcMs(Date.UTC(2026, 6, 21, 10, 5, 0)));
  });
});
