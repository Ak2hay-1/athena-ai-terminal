import { describe, expect, it, beforeEach } from "vitest";
import {
  appendCachedCandle,
  candleSeriesCacheStats,
  getCachedSeries,
  invalidateCachedSeries,
  putCachedSeries,
} from "@/lib/candle-series-cache";
import type { Candle } from "@/types";

function bar(time: string, close: number): Candle {
  return {
    symbol: "EURUSD",
    timeframe: "M5",
    time,
    open: close,
    high: close + 0.01,
    low: close - 0.01,
    close,
    tick_volume: 1,
  };
}

describe("candle-series-cache", () => {
  beforeEach(() => {
    invalidateCachedSeries();
  });

  it("returns null on miss and hydrates on put", () => {
    expect(getCachedSeries("EURUSD", "M5")).toBeNull();
    putCachedSeries("EURUSD", "M5", [
      bar("2024-01-01T00:00:00Z", 1.1),
      bar("2024-01-01T00:05:00Z", 1.2),
    ]);
    const hit = getCachedSeries("EURUSD", "M5");
    expect(hit).toHaveLength(2);
    expect(hit?.[1].close).toBe(1.2);
  });

  it("replaces same-bucket closed candle on append", () => {
    putCachedSeries("EURUSD", "M5", [bar("2024-01-01T00:00:00Z", 1.1)]);
    appendCachedCandle(
      "EURUSD",
      "M5",
      bar("2024-01-01T00:00:00Z", 1.15),
    );
    const hit = getCachedSeries("EURUSD", "M5");
    expect(hit).toHaveLength(1);
    expect(hit?.[0].close).toBe(1.15);
  });

  it("tracks stats and invalidates by symbol", () => {
    putCachedSeries("EURUSD", "M5", [bar("2024-01-01T00:00:00Z", 1.1)]);
    putCachedSeries("GBPUSD", "M5", [bar("2024-01-01T00:00:00Z", 1.2)]);
    expect(candleSeriesCacheStats().series).toBe(2);
    invalidateCachedSeries("EURUSD");
    expect(getCachedSeries("EURUSD", "M5")).toBeNull();
    expect(getCachedSeries("GBPUSD", "M5")).toHaveLength(1);
  });
});
