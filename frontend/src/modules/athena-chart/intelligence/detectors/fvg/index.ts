import type { Candlestick } from "../../../types";
import type { FairValueGap } from "../../types";
import { makeId, scoreOf, trace } from "../../utils/scoring";

/** 3-candle FVG: extend until filled. */
export function detectFairValueGaps(candles: Candlestick[]): FairValueGap[] {
  const gaps: FairValueGap[] = [];
  for (let i = 1; i < candles.length - 1; i++) {
    const a = candles[i - 1];
    const c = candles[i + 1];
    // Bullish FVG: candle[i-1].high < candle[i+1].low
    if (a.high < c.low) {
      gaps.push(buildFvg("bullish", a.high, c.low, i, candles));
    }
    // Bearish FVG: candle[i-1].low > candle[i+1].high
    if (a.low > c.high) {
      gaps.push(buildFvg("bearish", c.high, a.low, i, candles));
    }
  }
  return gaps.slice(-24);
}

function buildFvg(
  bias: "bullish" | "bearish",
  bottom: number,
  top: number,
  midIndex: number,
  candles: Candlestick[],
): FairValueGap {
  const size = Math.abs(top - bottom) || 1e-9;
  let fill = 0;
  let endIndex = candles.length - 1;
  for (let j = midIndex + 2; j < candles.length; j++) {
    const x = candles[j];
    if (bias === "bullish") {
      if (x.low < top) {
        fill = Math.max(fill, (top - Math.max(x.low, bottom)) / size);
      }
      if (x.low <= bottom) {
        fill = 1;
        endIndex = j;
        break;
      }
    } else {
      if (x.high > bottom) {
        fill = Math.max(fill, (Math.min(x.high, top) - bottom) / size);
      }
      if (x.high >= top) {
        fill = 1;
        endIndex = j;
        break;
      }
    }
  }
  const status =
    fill >= 1 ? "filled" : fill > 0.15 ? "partial" : "active";
  const strength = Math.min(100, 40 + (size / (candles[midIndex].close || 1)) * 8000);
  return {
    id: makeId("fvg-"),
    bias,
    top,
    bottom,
    startIndex: midIndex - 1,
    endIndex,
    fillRatio: Math.min(1, fill),
    ...scoreOf({
      confidence: strength * (status === "filled" ? 0.4 : 1),
      strength,
      ageBars: candles.length - 1 - midIndex,
      status: status === "partial" ? "partial" : status === "filled" ? "filled" : "active",
    }),
    trace: trace("fvg.3candle.v1", [midIndex - 1, midIndex, midIndex + 1], bias),
    createdAt: Date.now(),
  };
}
