import type { Candlestick, MagnetMode } from "../../types";

export function snapPriceAdvanced(
  candles: Candlestick[],
  index: number,
  price: number,
  mode: MagnetMode,
): number {
  if (mode === "off" || candles.length === 0) return price;
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
  if (mode === "strong") return best;
  // Weak: snap only if within ~0.15% of price span of that candle
  const range = Math.max(1e-12, c.high - c.low);
  const threshold = range * 0.35 || Math.abs(price) * 0.0002;
  return dist <= threshold ? best : price;
}
