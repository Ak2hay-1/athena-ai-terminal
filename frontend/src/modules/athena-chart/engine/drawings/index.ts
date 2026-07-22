import type { Candlestick, ChartDrawing } from "../../types";
import { candleTimeSec } from "../../utils/format";
import { uid } from "../../utils/uid";

export function snapPrice(
  candles: Candlestick[],
  index: number,
  price: number,
  magnet: boolean,
): number {
  if (!magnet || candles.length === 0) return price;
  const i = Math.max(0, Math.min(candles.length - 1, Math.round(index)));
  const c = candles[i];
  const candidates = [c.open, c.high, c.low, c.close];
  let best = candidates[0];
  let dist = Infinity;
  for (const p of candidates) {
    const d = Math.abs(p - price);
    if (d < dist) {
      dist = d;
      best = p;
    }
  }
  return best;
}

export function createHlineDrawing(price: number): ChartDrawing {
  return { id: uid(), type: "hline", price };
}

export function createSegmentDrawing(
  type: "trend" | "ray" | "rect" | "fib",
  c1: Candlestick,
  p1: number,
  c2: Candlestick,
  p2: number,
): ChartDrawing {
  return {
    id: uid(),
    type,
    t1: candleTimeSec(c1.time),
    p1,
    t2: candleTimeSec(c2.time),
    p2,
  };
}

/** Map terminal toolbar tools onto engine-supported drawing tools. */
export function normalizeTool(
  tool: string,
): "cursor" | "trend" | "hline" | "ray" | "rect" | "fib" | "hand" | "zoom" | "crosshair" {
  switch (tool) {
    case "crosshair":
    case "hand":
    case "zoom":
    case "cursor":
    case "trend":
    case "hline":
    case "ray":
    case "rect":
    case "fib":
      return tool;
    case "vline":
    case "circle":
    case "text":
    case "arrow":
    case "measure":
    case "erase":
    case "magnet":
      return "cursor";
    default:
      return "cursor";
  }
}
