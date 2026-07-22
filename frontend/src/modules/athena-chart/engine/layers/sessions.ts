import type { AthenaChartTheme } from "../../theme";
import type { PaintContext } from "./context";
import { candleTimeSec } from "../../utils/format";

export const SESSION_DEFS = [
  { id: "sydney", name: "Sydney", openUtc: 21, closeUtc: 6, color: "rgba(56,189,248,0.06)" },
  { id: "tokyo", name: "Tokyo", openUtc: 0, closeUtc: 9, color: "rgba(168,85,247,0.06)" },
  { id: "london", name: "London", openUtc: 7, closeUtc: 16, color: "rgba(34,197,94,0.06)" },
  { id: "newyork", name: "New York", openUtc: 12, closeUtc: 21, color: "rgba(255,107,0,0.07)" },
] as const;

function hourInSession(hour: number, open: number, close: number): boolean {
  if (open < close) return hour >= open && hour < close;
  return hour >= open || hour < close;
}

/** Market session background bands (timezone-aware via candle UTC times). */
export function drawSessions(
  ctx: PaintContext,
  flags: Record<string, boolean>,
): void {
  const { r, candles, viewport, layout } = ctx;
  if (!candles.length) return;
  const { start, end } = viewport.visibleRange(candles.length);

  for (const sess of SESSION_DEFS) {
    if (flags[sess.id] === false) continue;
    let runStart = -1;
    for (let i = start; i <= end; i++) {
      const c = candles[i];
      const hour = c ? new Date(c.time).getUTCHours() : -1;
      const active = c ? hourInSession(hour, sess.openUtc, sess.closeUtc) : false;
      if (active && runStart < 0) runStart = i;
      if ((!active || i === end) && runStart >= 0) {
        const endIdx = active && i === end ? i : i - 1;
        const x1 = viewport.indexToX(runStart, layout.plotLeft, layout.plotWidth);
        const x2 = viewport.indexToX(endIdx + 1, layout.plotLeft, layout.plotWidth);
        r.setFillStyle(sess.color);
        r.fillRect(x1, layout.mainTop, Math.max(1, x2 - x1), layout.mainH);
        runStart = -1;
      }
    }
  }
  void candleTimeSec;
}

export type { AthenaChartTheme };
