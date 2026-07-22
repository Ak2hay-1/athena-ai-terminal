import type { Candlestick } from "../types";
import { TF_MINUTES, normalizeTimeframe } from "../utils/timeframes";

function hashSeed(symbol: string): number {
  let h = 2166136261;
  for (let i = 0; i < symbol.length; i++) {
    h ^= symbol.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function mulberry32(seed: number) {
  return () => {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function basePrice(symbol: string): number {
  const upper = symbol.toUpperCase();
  if (upper.startsWith("XAU")) return 2650;
  if (upper.startsWith("XAG")) return 31;
  if (upper.includes("JPY")) return 150;
  return 1.085;
}

/** Generate base M1 series then aggregate to target TF (mock). */
export function generateMockCandles(params: {
  symbol: string;
  timeframe: string;
  count?: number;
  endTime?: Date;
}): Candlestick[] {
  const { symbol, endTime = new Date() } = params;
  const tf = normalizeTimeframe(params.timeframe);
  const minutes = TF_MINUTES[tf] ?? 5;
  const count = params.count ?? Math.min(2000, Math.max(200, Math.floor(500 * (5 / Math.max(minutes, 0.5)))));

  // Build from finer base when aggregating
  const baseMinutes = minutes < 1 ? minutes : 1;
  const baseCount =
    minutes <= 1 ? count : Math.min(50_000, Math.ceil(count * (minutes / baseMinutes)));
  const rand = mulberry32(hashSeed(`${symbol}:M1`));
  let price = basePrice(symbol);
  const volatility = price > 100 ? price * 0.0008 : price * 0.0004;
  const base: Candlestick[] = [];
  const endMs = endTime.getTime();

  for (let i = baseCount - 1; i >= 0; i--) {
    const t = new Date(endMs - i * baseMinutes * 60_000);
    const drift = (rand() - 0.48) * volatility;
    const open = price;
    const close = Math.max(0.0001, open + drift);
    const wick = volatility * (0.3 + rand());
    const high = Math.max(open, close) + wick * rand();
    const low = Math.min(open, close) - wick * rand();
    base.push({
      symbol: symbol.toUpperCase(),
      timeframe: "1M",
      time: t.toISOString(),
      open,
      high,
      low,
      close,
      tick_volume: Math.floor(50 + rand() * 400),
    });
    price = close;
  }

  if (minutes <= 1) {
    return base.slice(-count).map((c) => ({ ...c, timeframe: tf }));
  }

  return aggregateCandles(base, minutes, tf).slice(-count);
}

export function aggregateCandles(
  candles: Candlestick[],
  bucketMinutes: number,
  timeframe: string,
): Candlestick[] {
  if (!candles.length) return [];
  const bucketMs = bucketMinutes * 60_000;
  const out: Candlestick[] = [];
  let bucketStart = Math.floor(new Date(candles[0].time).getTime() / bucketMs) * bucketMs;
  let open = candles[0].open;
  let high = candles[0].high;
  let low = candles[0].low;
  let close = candles[0].close;
  let vol = candles[0].tick_volume;
  let symbol = candles[0].symbol;

  const flush = (t: number) => {
    out.push({
      symbol,
      timeframe,
      time: new Date(t).toISOString(),
      open,
      high,
      low,
      close,
      tick_volume: vol,
    });
  };

  for (const c of candles) {
    const ts = new Date(c.time).getTime();
    const b = Math.floor(ts / bucketMs) * bucketMs;
    if (b !== bucketStart) {
      flush(bucketStart);
      bucketStart = b;
      open = c.open;
      high = c.high;
      low = c.low;
      close = c.close;
      vol = c.tick_volume;
      symbol = c.symbol;
    } else {
      high = Math.max(high, c.high);
      low = Math.min(low, c.low);
      close = c.close;
      vol += c.tick_volume;
    }
  }
  flush(bucketStart);
  return out;
}

export const marketDataService = {
  getCandles: generateMockCandles,
  aggregateCandles,
};
