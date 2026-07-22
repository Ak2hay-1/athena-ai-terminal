import type { Candlestick } from "../../../types";
import type { SessionInfo } from "../../types";

const DEFS = [
  { id: "sydney", name: "Sydney", open: 21, close: 6 },
  { id: "tokyo", name: "Tokyo", open: 0, close: 9 },
  { id: "london", name: "London", open: 7, close: 16 },
  { id: "newyork", name: "New York", open: 12, close: 21 },
] as const;

function inSession(hour: number, open: number, close: number): boolean {
  if (open < close) return hour >= open && hour < close;
  return hour >= open || hour < close;
}

export function detectSessions(candles: Candlestick[]): SessionInfo[] {
  if (!candles.length) return [];
  const nowHour = new Date(candles[candles.length - 1].time).getUTCHours();
  return DEFS.map((d) => {
    const inSess = candles.filter((c) => {
      const h = new Date(c.time).getUTCHours();
      return inSession(h, d.open, d.close);
    });
    const slice = inSess.length ? inSess.slice(-48) : [];
    const open = slice[0]?.open ?? 0;
    const close = slice[slice.length - 1]?.close ?? 0;
    const high = slice.length ? Math.max(...slice.map((c) => c.high)) : 0;
    const low = slice.length ? Math.min(...slice.map((c) => c.low)) : 0;
    const killZone =
      (d.id === "london" && nowHour >= 7 && nowHour < 10) ||
      (d.id === "newyork" && nowHour >= 12 && nowHour < 15);
    return {
      id: d.id,
      name: d.name,
      active: inSession(nowHour, d.open, d.close),
      open,
      high,
      low,
      close,
      killZone,
    };
  });
}
