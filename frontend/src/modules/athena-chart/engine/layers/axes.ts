import {
  candleTimeSec,
  formatPriceLabel,
  formatTimeLabel,
  niceTicks,
} from "../../utils/format";
import { RIGHT_AXIS, BOTTOM_AXIS, type PaintContext } from "./context";

export function drawAxes(ctx: PaintContext, start: number, end: number): void {
  const { r, theme, layout, width, height, candles, viewport, priceMin, priceMax, priceY, symbol } =
    ctx;

  r.setFillStyle(theme.background);
  r.fillRect(layout.plotWidth, 0, RIGHT_AXIS, height);
  r.fillRect(0, layout.plotBottom, width, BOTTOM_AXIS);

  r.setFillStyle(theme.text);
  r.setFont(theme.fontSmall);
  const ticks = niceTicks(priceMin, priceMax, 6);
  for (const p of ticks) {
    const y = priceY(p, layout.mainTop, layout.mainH);
    r.fillText(formatPriceLabel(p, symbol), layout.plotWidth + 6, y + 3);
  }

  const first = candles[Math.max(0, start)];
  const last = candles[Math.min(candles.length - 1, Math.max(start, end - 1))];
  const spanSec =
    first && last
      ? Math.max(60, candleTimeSec(last.time) - candleTimeSec(first.time))
      : 86_400;

  const step = Math.max(1, Math.floor(viewport.span / 6));
  for (let i = Math.ceil(start / step) * step; i < end; i += step) {
    const c = candles[i];
    if (!c) continue;
    const x = viewport.indexToX(i + 0.5, layout.plotLeft, layout.plotWidth);
    const label = formatTimeLabel(candleTimeSec(c.time), spanSec);
    const offset = Math.min(40, Math.max(14, label.length * 3.2));
    r.fillText(label, x - offset / 2, layout.plotBottom + 18);
  }
}

export function drawLastPrice(ctx: PaintContext): void {
  const last = ctx.candles[ctx.candles.length - 1];
  if (!last) return;
  const { r, theme, layout, priceY, symbol } = ctx;
  const y = priceY(last.close, layout.mainTop, layout.mainH);
  r.setStrokeStyle(theme.lastPrice);
  r.setLineDash([4, 3]);
  r.beginPath();
  r.moveTo(0, y);
  r.lineTo(layout.plotWidth, y);
  r.stroke();
  r.setLineDash([]);
  r.setFillStyle(theme.lastPrice);
  r.fillRect(layout.plotWidth, y - 8, RIGHT_AXIS, 16);
  r.setFillStyle("#000");
  r.setFont(theme.fontSmall);
  r.fillText(formatPriceLabel(last.close, symbol), layout.plotWidth + 4, y + 3);
}
