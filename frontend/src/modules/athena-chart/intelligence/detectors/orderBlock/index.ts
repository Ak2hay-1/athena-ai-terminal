import type { Candlestick } from "../../../types";
import type { OrderBlock } from "../../types";
import { makeId, scoreOf, trace } from "../../utils/scoring";

export function detectOrderBlocks(candles: Candlestick[]): OrderBlock[] {
  const blocks: OrderBlock[] = [];
  if (candles.length < 8) return blocks;

  for (let i = 2; i < candles.length - 2; i++) {
    const c = candles[i];
    const next = candles[i + 1];
    const prev = candles[i - 1];
    const bearishOb =
      c.close < c.open &&
      next.close > c.high &&
      next.close > prev.high;
    const bullishOb =
      c.close > c.open &&
      next.close < c.low &&
      next.close < prev.low;

    if (bullishOb || bearishOb) {
      // ICT-style: last opposing candle before impulse
      const bias = next.close > c.close ? "bullish" : "bearish";
      const obCandle = bias === "bullish" ? c : c;
      const top = Math.max(obCandle.open, obCandle.close, obCandle.high);
      const bottom = Math.min(obCandle.open, obCandle.close, obCandle.low);
      let mitigated = false;
      let invalid = false;
      let retests = 0;
      for (let j = i + 2; j < candles.length; j++) {
        const x = candles[j];
        if (x.low <= top && x.high >= bottom) {
          retests++;
          mitigated = true;
        }
        if (bias === "bullish" && x.close < bottom) invalid = true;
        if (bias === "bearish" && x.close > top) invalid = true;
      }
      const breaker = mitigated && !invalid && retests >= 1;
      const strength = Math.min(
        100,
        55 + (breaker ? 10 : 0) + Math.min(30, (top - bottom) / (candles[i].close || 1) * 5000),
      );
      blocks.push({
        id: makeId("ob-"),
        bias: bias as "bullish" | "bearish",
        top,
        bottom,
        startIndex: i,
        endIndex: i,
        breaker,
        mitigated,
        invalid,
        ...scoreOf({
          confidence: strength,
          strength,
          retests,
          ageBars: candles.length - 1 - i,
          status: invalid ? "invalid" : mitigated ? "mitigated" : "active",
        }),
        trace: trace("ob.impulse.v1", [i, i + 1], bias),
        createdAt: Date.now(),
      });
    }
  }

  return blocks.filter((b) => !b.invalid).slice(-16);
}
