import type { Candle } from "@/types";

export type ChartType = "candles" | "hollow" | "line" | "area";

export type DrawingTool =
  | "cursor"
  | "trend"
  | "hline"
  | "ray"
  | "rect"
  | "fib";

export interface IndicatorFlags {
  ema20: boolean;
  ema50: boolean;
  sma20: boolean;
  sma50: boolean;
  sma200: boolean;
  bollinger: boolean;
  vwap: boolean;
  atr: boolean;
  rsi: boolean;
  macd: boolean;
  volume: boolean;
  priceLine: boolean;
}

export const DEFAULT_INDICATORS: IndicatorFlags = {
  ema20: false,
  ema50: false,
  sma20: false,
  sma50: false,
  sma200: false,
  bollinger: false,
  vwap: false,
  atr: false,
  rsi: false,
  macd: false,
  volume: true,
  priceLine: true,
};

export interface LinePoint {
  time: number;
  value: number;
}

function toTs(time: string): number {
  return Math.floor(new Date(time).getTime() / 1000);
}

export function computeSma(
  values: number[],
  period: number,
): Array<number | null> {
  const out: Array<number | null> = Array(values.length).fill(null);
  if (values.length < period) return out;
  let sum = 0;
  for (let i = 0; i < values.length; i++) {
    sum += values[i];
    if (i >= period) sum -= values[i - period];
    if (i >= period - 1) out[i] = sum / period;
  }
  return out;
}

export function computeEma(
  values: number[],
  period: number,
): Array<number | null> {
  const out: Array<number | null> = Array(values.length).fill(null);
  if (values.length < period) return out;
  const k = 2 / (period + 1);
  let sum = 0;
  for (let i = 0; i < period; i++) sum += values[i];
  let ema = sum / period;
  out[period - 1] = ema;
  for (let i = period; i < values.length; i++) {
    ema = values[i] * k + ema * (1 - k);
    out[i] = ema;
  }
  return out;
}

export function computeBollinger(
  closes: number[],
  period = 20,
  mult = 2,
): {
  mid: Array<number | null>;
  upper: Array<number | null>;
  lower: Array<number | null>;
} {
  const mid = computeSma(closes, period);
  const upper: Array<number | null> = Array(closes.length).fill(null);
  const lower: Array<number | null> = Array(closes.length).fill(null);
  for (let i = period - 1; i < closes.length; i++) {
    const slice = closes.slice(i - period + 1, i + 1);
    const mean = mid[i];
    if (mean == null) continue;
    const variance =
      slice.reduce((acc, v) => acc + (v - mean) ** 2, 0) / period;
    const std = Math.sqrt(variance);
    upper[i] = mean + mult * std;
    lower[i] = mean - mult * std;
  }
  return { mid, upper, lower };
}

export function computeRsi(
  closes: number[],
  period = 14,
): Array<number | null> {
  const out: Array<number | null> = Array(closes.length).fill(null);
  if (closes.length <= period) return out;
  let gains = 0;
  let losses = 0;
  for (let i = 1; i <= period; i++) {
    const diff = closes[i] - closes[i - 1];
    if (diff >= 0) gains += diff;
    else losses -= diff;
  }
  let avgGain = gains / period;
  let avgLoss = losses / period;
  out[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  for (let i = period + 1; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1];
    const gain = diff > 0 ? diff : 0;
    const loss = diff < 0 ? -diff : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    out[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return out;
}

export function computeMacd(
  closes: number[],
  fast = 12,
  slow = 26,
  signal = 9,
): {
  macd: Array<number | null>;
  signal: Array<number | null>;
  hist: Array<number | null>;
} {
  const emaFast = computeEma(closes, fast);
  const emaSlow = computeEma(closes, slow);
  const macd: Array<number | null> = Array(closes.length).fill(null);
  for (let i = 0; i < closes.length; i++) {
    if (emaFast[i] != null && emaSlow[i] != null) {
      macd[i] = (emaFast[i] as number) - (emaSlow[i] as number);
    }
  }
  const macdValues = macd.map((v) => v ?? 0);
  // Signal EMA only meaningful after slow period
  const signalLine = computeEma(macdValues, signal);
  // Zero out early nulls where MACD itself is null
  for (let i = 0; i < signalLine.length; i++) {
    if (macd[i] == null) signalLine[i] = null;
  }
  const hist: Array<number | null> = Array(closes.length).fill(null);
  for (let i = 0; i < closes.length; i++) {
    if (macd[i] != null && signalLine[i] != null) {
      hist[i] = (macd[i] as number) - (signalLine[i] as number);
    }
  }
  return { macd, signal: signalLine, hist };
}

export function computeAtr(
  candles: Candle[],
  period = 14,
): Array<number | null> {
  const out: Array<number | null> = Array(candles.length).fill(null);
  if (candles.length < 2) return out;
  const tr: number[] = [candles[0].high - candles[0].low];
  for (let i = 1; i < candles.length; i++) {
    const c = candles[i];
    const prev = candles[i - 1];
    tr.push(
      Math.max(
        c.high - c.low,
        Math.abs(c.high - prev.close),
        Math.abs(c.low - prev.close),
      ),
    );
  }
  if (tr.length < period) return out;
  let sum = 0;
  for (let i = 0; i < period; i++) sum += tr[i];
  let atr = sum / period;
  out[period - 1] = atr;
  for (let i = period; i < tr.length; i++) {
    atr = (atr * (period - 1) + tr[i]) / period;
    out[i] = atr;
  }
  return out;
}

export function computeVwap(candles: Candle[]): Array<number | null> {
  const out: Array<number | null> = Array(candles.length).fill(null);
  let cumPv = 0;
  let cumVol = 0;
  for (let i = 0; i < candles.length; i++) {
    const c = candles[i];
    const vol = c.tick_volume || 0;
    const typical = (c.high + c.low + c.close) / 3;
    cumPv += typical * vol;
    cumVol += vol;
    out[i] = cumVol > 0 ? cumPv / cumVol : typical;
  }
  return out;
}

export function toLineData(
  candles: Candle[],
  values: Array<number | null>,
): LinePoint[] {
  const points: LinePoint[] = [];
  for (let i = 0; i < candles.length; i++) {
    const v = values[i];
    if (v == null || !Number.isFinite(v)) continue;
    points.push({ time: toTs(candles[i].time), value: v });
  }
  return points;
}

export function barsForZoomPreset(
  timeframe: string,
  preset: "1D" | "1W" | "1M" | "ALL",
): number | null {
  if (preset === "ALL") return null;
  const minutes: Record<string, number> = {
    M1: 1,
    M5: 5,
    M15: 15,
    M30: 30,
    H1: 60,
    H4: 240,
    D1: 1440,
  };
  const barMin = minutes[timeframe.toUpperCase()] ?? 5;
  const targetMin =
    preset === "1D" ? 1440 : preset === "1W" ? 10080 : 43200;
  return Math.max(20, Math.ceil(targetMin / barMin));
}
