import { priceDigitsFor } from "@/constants/markets";

export function candleTimeSec(time: string): number {
  return Math.floor(new Date(time).getTime() / 1000);
}

export function niceTicks(min: number, max: number, count = 6): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) {
    return [min || 0];
  }
  const span = max - min;
  const step = Math.pow(10, Math.floor(Math.log10(span / count)));
  const err = count / (span / step);
  let niceStep = step;
  if (err <= 0.15) niceStep = step * 10;
  else if (err <= 0.35) niceStep = step * 5;
  else if (err <= 0.75) niceStep = step * 2;
  const start = Math.ceil(min / niceStep) * niceStep;
  const ticks: number[] = [];
  for (let v = start; v <= max + niceStep * 0.001; v += niceStep) {
    ticks.push(v);
  }
  return ticks;
}

/** Full instrument precision for the price axis / crosshair. */
export function formatPriceLabel(v: number, symbol?: string): string {
  if (!Number.isFinite(v)) return "";
  const digits = symbol ? priceDigitsFor(symbol, v) : guessDigits(v);
  return v.toFixed(digits);
}

function guessDigits(v: number): number {
  const abs = Math.abs(v);
  if (abs >= 100) return 2;
  if (abs >= 10) return 3;
  if (abs >= 1) return 5;
  return 5;
}

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
] as const;

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

/**
 * Adaptive local date/time labels for the chart time axis.
 * Input is UTC epoch seconds; display uses local timezone.
 */
export function formatTimeLabel(sec: number, spanSec = 86_400): string {
  const d = new Date(sec * 1000);
  if (!Number.isFinite(d.getTime())) return "";

  const month = MONTHS[d.getMonth()];
  const day = d.getDate();
  const year = d.getFullYear();
  const hh = pad2(d.getHours());
  const mm = pad2(d.getMinutes());

  // Intraday (< ~2 days): clock time; include day when spanning midnight
  if (spanSec <= 86_400 * 1.5) {
    if (spanSec <= 6 * 3600) return `${hh}:${mm}`;
    return `${hh}:${mm}`;
  }
  // Multi-day: date
  if (spanSec < 40 * 86_400) {
    return `${month} ${day}`;
  }
  // Multi-month: month
  if (spanSec < 400 * 86_400) {
    return `${month}`;
  }
  return `${month} ${year}`;
}

/** TradingView-style crosshair time tooltip (local). */
export function formatCrosshairTime(sec: number): { date: string; time: string } {
  const d = new Date(sec * 1000);
  if (!Number.isFinite(d.getTime())) return { date: "", time: "" };
  const date = `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
  const time = `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`;
  return { date, time };
}
