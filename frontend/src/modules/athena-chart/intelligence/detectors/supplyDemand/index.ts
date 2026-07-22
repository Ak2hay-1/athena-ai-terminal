import type { Candlestick } from "../../../types";
import type { Zone } from "../../types";
import { makeId, scoreOf, trace } from "../../utils/scoring";

/** Supply / Demand from impulse base candles. */
export function detectSupplyDemand(candles: Candlestick[]): Zone[] {
  const zones: Zone[] = [];
  if (candles.length < 10) return zones;

  for (let i = 3; i < candles.length - 3; i++) {
    const c = candles[i];
    const body = Math.abs(c.close - c.open);
    const range = c.high - c.low || 1e-9;
    const next = candles[i + 1];
    const next2 = candles[i + 2];
    const impulseUp = next.close > c.high && next2.close > next.close;
    const impulseDown = next.close < c.low && next2.close < next.close;
    const base = body / range < 0.45;

    if (base && impulseUp) {
      zones.push(makeZone("demand", c, i, candles));
    }
    if (base && impulseDown) {
      zones.push(makeZone("supply", c, i, candles));
    }
  }

  return zones.slice(-20);
}

function makeZone(
  kind: "demand" | "supply",
  c: Candlestick,
  i: number,
  candles: Candlestick[],
): Zone {
  const top = Math.max(c.open, c.close);
  const bottom = Math.min(c.open, c.close);
  let retests = 0;
  let mitigated = false;
  let invalid = false;
  for (let j = i + 3; j < candles.length; j++) {
    const x = candles[j];
    if (x.low <= top && x.high >= bottom) {
      retests++;
      mitigated = true;
    }
    if (kind === "demand" && x.close < bottom) invalid = true;
    if (kind === "supply" && x.close > top) invalid = true;
  }
  const freshness = Math.max(0, 100 - retests * 20);
  const strength = Math.min(100, 50 + freshness * 0.3 + (invalid ? 0 : 20));
  return {
    id: makeId("zn-"),
    kind,
    top,
    bottom,
    startIndex: i,
    endIndex: i,
    mitigated,
    invalid,
    freshness,
    ...scoreOf({
      confidence: strength,
      strength,
      retests,
      ageBars: candles.length - 1 - i,
      status: invalid ? "invalid" : mitigated ? "mitigated" : "active",
    }),
    trace: trace("sd.impulse.v1", [i, i + 1, i + 2], kind),
    createdAt: Date.now(),
  };
}
