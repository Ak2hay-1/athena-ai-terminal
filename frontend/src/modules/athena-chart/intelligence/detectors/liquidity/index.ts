import type { Candlestick } from "../../../types";
import type { LiquidityPool, SwingPoint } from "../../types";
import { makeId, scoreOf, trace } from "../../utils/scoring";

export function detectLiquidity(
  candles: Candlestick[],
  swings: SwingPoint[],
): LiquidityPool[] {
  const pools: LiquidityPool[] = [];
  if (candles.length < 10) return pools;

  const atr =
    candles.slice(-30).reduce((s, c) => s + (c.high - c.low), 0) /
    Math.min(30, candles.length);
  const eqTol = atr * 0.12;

  const highs = swings.filter((s) => s.kind === "high");
  const lows = swings.filter((s) => s.kind === "low");

  for (let i = 1; i < highs.length; i++) {
    if (Math.abs(highs[i].price - highs[i - 1].price) <= eqTol) {
      pools.push(
        pool("equal_highs", highs[i].price, highs[i].index, highs[i].time, [
          highs[i - 1].index,
          highs[i].index,
        ], 70),
      );
    }
  }
  for (let i = 1; i < lows.length; i++) {
    if (Math.abs(lows[i].price - lows[i - 1].price) <= eqTol) {
      pools.push(
        pool("equal_lows", lows[i].price, lows[i].index, lows[i].time, [
          lows[i - 1].index,
          lows[i].index,
        ], 70),
      );
    }
  }

  // Sweeps: wick beyond swing then close back inside
  const lastSwingHigh = [...highs].reverse()[0];
  const lastSwingLow = [...lows].reverse()[0];
  for (let i = Math.max(1, candles.length - 40); i < candles.length; i++) {
    const c = candles[i];
    if (lastSwingHigh && c.high > lastSwingHigh.price + eqTol * 0.5 && c.close < lastSwingHigh.price) {
      pools.push(
        pool("sweep", lastSwingHigh.price, i, c.time, [lastSwingHigh.index, i], 80, "stop_hunt"),
      );
    }
    if (lastSwingLow && c.low < lastSwingLow.price - eqTol * 0.5 && c.close > lastSwingLow.price) {
      pools.push(
        pool("sweep", lastSwingLow.price, i, c.time, [lastSwingLow.index, i], 80, "stop_hunt"),
      );
    }
  }

  // Resting / internal / external pools at recent extremes
  if (lastSwingHigh) {
    pools.push(
      pool("external", lastSwingHigh.price, lastSwingHigh.index, lastSwingHigh.time, [
        lastSwingHigh.index,
      ], 65),
    );
    pools.push(
      pool("resting", lastSwingHigh.price, lastSwingHigh.index, lastSwingHigh.time, [
        lastSwingHigh.index,
      ], 55),
    );
  }
  if (lastSwingLow) {
    pools.push(
      pool("internal", lastSwingLow.price, lastSwingLow.index, lastSwingLow.time, [
        lastSwingLow.index,
      ], 50),
    );
  }

  return pools
    .sort((a, b) => b.importance - a.importance)
    .slice(0, 30);
}

function pool(
  kind: LiquidityPool["kind"],
  price: number,
  index: number,
  time: string,
  indices: number[],
  importance: number,
  alt?: LiquidityPool["kind"],
): LiquidityPool {
  const k = alt ?? kind;
  return {
    id: makeId("liq-"),
    kind: k,
    price,
    index,
    time,
    importance,
    ...scoreOf({ confidence: importance, strength: importance, ageBars: 0 }),
    trace: trace("liquidity.v1", indices, k),
    createdAt: Date.now(),
  };
}
