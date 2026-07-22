import { describe, expect, it } from "vitest";
import { applyLiveCandleUpdate } from "@/lib/candle-history";
import type { Candle } from "@/types";

function c(partial: Partial<Candle> & { time: string; close: number }): Candle {
  return {
    symbol: "XAUUSD",
    timeframe: "M5",
    open: partial.open ?? partial.close,
    high: partial.high ?? partial.close,
    low: partial.low ?? partial.close,
    tick_volume: 1,
    ...partial,
  };
}

describe("applyLiveCandleUpdate bucket guard", () => {
  it("does not stretch an old bucket when a new mid arrives with a later bucket time", () => {
    const evening = "2026-07-20T23:00:00.000Z";
    const morning = "2026-07-21T08:00:00.000Z";
    const current = [
      c({
        time: evening,
        open: 2650,
        high: 2651,
        low: 2649,
        close: 2650,
      }),
    ];
    const next = applyLiveCandleUpdate(
      current,
      c({
        time: morning,
        open: 2680,
        high: 2680,
        low: 2680,
        close: 2680,
      }),
    );
    expect(next).toHaveLength(2);
    expect(next[0].high).toBe(2651);
    expect(next[0].low).toBe(2649);
    expect(next[1].close).toBe(2680);
  });

  it("replaces same bucket in place", () => {
    const t = "2026-07-21T10:05:00.000Z";
    const current = [c({ time: t, close: 1.1, high: 1.1, low: 1.1 })];
    const next = applyLiveCandleUpdate(
      current,
      c({ time: t, close: 1.12, high: 1.13, low: 1.09 }),
    );
    expect(next).toHaveLength(1);
    expect(next[0].close).toBe(1.12);
    expect(next[0].high).toBe(1.13);
  });
});
