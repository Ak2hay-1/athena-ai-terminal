import type { Candlestick } from "../../../types";
import type { Imbalance } from "../../types";
import { makeId, scoreOf, trace } from "../../utils/scoring";

export function detectImbalances(candles: Candlestick[]): Imbalance[] {
  const out: Imbalance[] = [];
  if (candles.length < 5) return out;
  const avgVol =
    candles.slice(-50).reduce((s, c) => s + c.tick_volume, 0) /
    Math.min(50, candles.length);

  for (let i = 1; i < candles.length; i++) {
    const c = candles[i];
    const prev = candles[i - 1];
    const gap = c.open - prev.close;
    const range = c.high - c.low || 1e-9;
    if (Math.abs(gap) > range * 0.35) {
      out.push({
        id: makeId("imb-"),
        kind: "price",
        index: i,
        gapSize: Math.abs(gap),
        direction: gap > 0 ? "bullish" : "bearish",
        ...scoreOf({
          confidence: Math.min(90, 50 + (Math.abs(gap) / range) * 20),
          strength: Math.min(100, (Math.abs(gap) / range) * 40),
          ageBars: candles.length - 1 - i,
        }),
        trace: trace("imbalance.price.v1", [i - 1, i]),
        createdAt: Date.now(),
      });
    }
    if (c.tick_volume > avgVol * 2.2) {
      out.push({
        id: makeId("imb-"),
        kind: "volume",
        index: i,
        gapSize: c.tick_volume / avgVol,
        direction: c.close >= c.open ? "bullish" : "bearish",
        ...scoreOf({
          confidence: 60,
          strength: Math.min(100, (c.tick_volume / avgVol) * 25),
          ageBars: candles.length - 1 - i,
        }),
        trace: trace("imbalance.volume.v1", [i]),
        createdAt: Date.now(),
      });
    }
    const mom = c.close - prev.close;
    if (Math.abs(mom) > range * 0.8) {
      out.push({
        id: makeId("imb-"),
        kind: "momentum",
        index: i,
        gapSize: Math.abs(mom),
        direction: mom > 0 ? "bullish" : "bearish",
        ...scoreOf({ confidence: 55, strength: 55, ageBars: candles.length - 1 - i }),
        trace: trace("imbalance.momentum.v1", [i]),
        createdAt: Date.now(),
      });
    }
  }
  return out.slice(-40);
}
