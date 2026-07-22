import type { Candlestick } from "../../../types";
import type { PatternHit, PatternKind, SwingPoint } from "../../types";
import { makeId, scoreOf, trace } from "../../utils/scoring";

export function detectPatterns(
  candles: Candlestick[],
  swings: SwingPoint[],
): PatternHit[] {
  const hits: PatternHit[] = [];
  if (swings.length < 4 || candles.length < 30) return hits;

  const highs = swings.filter((s) => s.kind === "high");
  const lows = swings.filter((s) => s.kind === "low");

  // Double top / bottom
  if (highs.length >= 2) {
    const a = highs[highs.length - 2];
    const b = highs[highs.length - 1];
    const atr = avgRange(candles);
    if (Math.abs(a.price - b.price) < atr * 0.35) {
      hits.push(pat("double_top", a.index, b.index, "bearish", 65, [a.index, b.index]));
    }
  }
  if (lows.length >= 2) {
    const a = lows[lows.length - 2];
    const b = lows[lows.length - 1];
    const atr = avgRange(candles);
    if (Math.abs(a.price - b.price) < atr * 0.35) {
      hits.push(pat("double_bottom", a.index, b.index, "bullish", 65, [a.index, b.index]));
    }
  }

  // Triangle / wedge from converging swings
  if (highs.length >= 3 && lows.length >= 3) {
    const h = highs.slice(-3);
    const l = lows.slice(-3);
    const hSlope = h[2].price - h[0].price;
    const lSlope = l[2].price - l[0].price;
    if (hSlope < 0 && lSlope > 0) {
      hits.push(pat("triangle", l[0].index, h[2].index, "neutral", 55, [...h, ...l].map((s) => s.index)));
      hits.push(pat("ascending_triangle", l[0].index, h[2].index, "bullish", 50, [l[0].index, h[2].index]));
    }
    if (hSlope < 0 && lSlope < 0) {
      hits.push(pat("descending_triangle", l[0].index, h[2].index, "bearish", 52, [l[0].index, h[2].index]));
      hits.push(pat("wedge", l[0].index, h[2].index, "bearish", 48, [l[0].index, h[2].index]));
    }
    if (hSlope > 0 && lSlope < 0) {
      hits.push(pat("expanding_triangle", l[0].index, h[2].index, "neutral", 45, [l[0].index, h[2].index]));
    }
  }

  // Channel / rectangle / flag / pennant (simplified)
  if (highs.length >= 2 && lows.length >= 2) {
    const h1 = highs[highs.length - 1].price;
    const h0 = highs[highs.length - 2].price;
    const l1 = lows[lows.length - 1].price;
    const l0 = lows[lows.length - 2].price;
    const atr = avgRange(candles);
    if (Math.abs(h1 - h0) < atr * 0.4 && Math.abs(l1 - l0) < atr * 0.4) {
      hits.push(
        pat(
          "rectangle",
          lows[lows.length - 2].index,
          highs[highs.length - 1].index,
          "neutral",
          58,
          [lows[lows.length - 2].index, highs[highs.length - 1].index],
        ),
      );
      hits.push(
        pat("channel", lows[lows.length - 2].index, highs[highs.length - 1].index, "neutral", 50, [
          lows[lows.length - 2].index,
          highs[highs.length - 1].index,
        ]),
      );
    }
    // Flag / pennant after impulse
    const impulse = candles.slice(-15);
    const move = impulse[impulse.length - 1].close - impulse[0].close;
    if (Math.abs(move) > atr * 3) {
      hits.push(
        pat(
          Math.abs(h1 - l1) < atr * 1.2 ? "pennant" : "flag",
          candles.length - 15,
          candles.length - 1,
          move > 0 ? "bullish" : "bearish",
          54,
          [candles.length - 15, candles.length - 1],
        ),
      );
    }
  }

  // Head & shoulders (3 highs, middle highest)
  if (highs.length >= 3) {
    const [a, b, c] = highs.slice(-3);
    if (b.price > a.price && b.price > c.price && Math.abs(a.price - c.price) < avgRange(candles) * 0.5) {
      hits.push(pat("head_shoulders", a.index, c.index, "bearish", 62, [a.index, b.index, c.index]));
    }
  }
  if (lows.length >= 3) {
    const [a, b, c] = lows.slice(-3);
    if (b.price < a.price && b.price < c.price && Math.abs(a.price - c.price) < avgRange(candles) * 0.5) {
      hits.push(pat("inv_head_shoulders", a.index, c.index, "bullish", 62, [a.index, b.index, c.index]));
    }
  }

  // Cup & handle rough: U-shape in closes
  const slice = candles.slice(-40);
  if (slice.length >= 30) {
    const mid = Math.floor(slice.length / 2);
    const left = slice[5].close;
    const bottom = Math.min(...slice.slice(10, mid + 5).map((c) => c.low));
    const right = slice[slice.length - 5].close;
    if (Math.abs(left - right) / left < 0.02 && bottom < left * 0.98) {
      hits.push(
        pat("cup_handle", candles.length - 40, candles.length - 1, "bullish", 48, [
          candles.length - 40,
          candles.length - 1,
        ]),
      );
    }
  }

  return hits;
}

function avgRange(candles: Candlestick[]): number {
  const n = Math.min(20, candles.length);
  return candles.slice(-n).reduce((s, c) => s + (c.high - c.low), 0) / n;
}

function pat(
  kind: PatternKind,
  startIndex: number,
  endIndex: number,
  direction: PatternHit["direction"],
  confidence: number,
  indices: number[],
): PatternHit {
  return {
    id: makeId("pat-"),
    kind,
    startIndex,
    endIndex,
    direction,
    ...scoreOf({ confidence, strength: confidence, ageBars: 0 }),
    trace: trace("pattern.v1", indices, kind),
    createdAt: Date.now(),
  };
}
