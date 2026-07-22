import { createDrawingObject } from "../engine/drawing/factory";
import type { DrawingObject } from "../types";

/** Stress harness — generate N drawings for FPS testing. */
export function generateStressDrawings(count: number, baseTime = Date.now() / 1000): DrawingObject[] {
  const out: DrawingObject[] = [];
  for (let i = 0; i < count; i++) {
    const t1 = baseTime - (count - i) * 60;
    const p1 = 100 + (i % 50) * 0.1;
    out.push(
      createDrawingObject(
        i % 5 === 0 ? "hline" : i % 3 === 0 ? "trend" : "rect",
        i % 5 === 0
          ? [{ t: t1, p: p1 }]
          : [
              { t: t1, p: p1 },
              { t: t1 + 300, p: p1 + 0.5 },
            ],
        { zIndex: i },
      ),
    );
  }
  return out;
}

export function generateStressCandles(count: number, symbol = "XAUUSD") {
  const candles = [];
  let price = 2650;
  const now = Date.now();
  for (let i = count - 1; i >= 0; i--) {
    const open = price;
    const close = open + (Math.random() - 0.5) * 2;
    candles.push({
      symbol,
      timeframe: "1M",
      time: new Date(now - i * 60_000).toISOString(),
      open,
      high: Math.max(open, close) + Math.random(),
      low: Math.min(open, close) - Math.random(),
      close,
      tick_volume: Math.floor(Math.random() * 200),
    });
    price = close;
  }
  return candles;
}
