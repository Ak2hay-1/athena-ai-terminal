import { candleTimeSec } from "../../utils/format";
import type { ChartDrawing, ChartMarker } from "../../types";
import type { PaintContext } from "./context";

export function drawMarkers(ctx: PaintContext): void {
  if (!ctx.markers.length) return;
  const { r, theme, layout, candles, viewport, priceY, markers } = ctx;
  const byTime = new Map(candles.map((c, i) => [candleTimeSec(c.time), i] as const));
  for (const m of markers) {
    const t = Math.floor(new Date(m.time).getTime() / 1000);
    let idx = byTime.get(t);
    if (idx == null) {
      let best = 0;
      let dist = Infinity;
      for (let i = 0; i < candles.length; i++) {
        const d = Math.abs(candleTimeSec(candles[i].time) - t);
        if (d < dist) {
          dist = d;
          best = i;
        }
      }
      idx = best;
    }
    if (idx < viewport.from - 1 || idx > viewport.to + 1) continue;
    const c = candles[idx];
    const x = viewport.indexToX(idx + 0.5, layout.plotLeft, layout.plotWidth);
    const above = m.position !== "belowBar";
    const y = priceY(above ? c.high : c.low, layout.mainTop, layout.mainH) + (above ? -10 : 10);
    r.setFillStyle(m.color ?? theme.crosshair);
    r.beginPath();
    if (m.shape === "arrowUp") {
      r.moveTo(x, y + 6);
      r.lineTo(x - 5, y - 2);
      r.lineTo(x + 5, y - 2);
    } else if (m.shape === "arrowDown") {
      r.moveTo(x, y - 6);
      r.lineTo(x - 5, y + 2);
      r.lineTo(x + 5, y + 2);
    } else {
      r.arc(x, y, 4, 0, Math.PI * 2);
    }
    r.fill();
    if (m.text) {
      r.setFont(theme.fontSmall);
      r.fillText(m.text, x + 6, y + 3);
    }
  }
}

function indexFromDrawingTime(candles: PaintContext["candles"], timeSec: number): number {
  let best = 0;
  let dist = Infinity;
  for (let i = 0; i < candles.length; i++) {
    const d = Math.abs(candleTimeSec(candles[i].time) - timeSec);
    if (d < dist) {
      dist = d;
      best = i;
    }
  }
  return best;
}

function paintDrawing(ctx: PaintContext, d: ChartDrawing): void {
  const { r, theme, layout, candles, viewport, priceY } = ctx;
  if (d.type === "hline") {
    const y = priceY(d.price, layout.mainTop, layout.mainH);
    r.setStrokeStyle(theme.drawingHline);
    r.setLineDash([4, 3]);
    r.beginPath();
    r.moveTo(0, y);
    r.lineTo(layout.plotWidth, y);
    r.stroke();
    r.setLineDash([]);
    return;
  }
  const i1 = indexFromDrawingTime(candles, d.t1);
  const i2 = indexFromDrawingTime(candles, d.t2);
  const x1 = viewport.indexToX(i1 + 0.5, layout.plotLeft, layout.plotWidth);
  const x2 = viewport.indexToX(i2 + 0.5, layout.plotLeft, layout.plotWidth);
  const y1 = priceY(d.p1, layout.mainTop, layout.mainH);
  const y2 = priceY(d.p2, layout.mainTop, layout.mainH);

  if (d.type === "trend") {
    r.setStrokeStyle(theme.drawingTrend);
    r.setLineWidth(1.5);
    r.beginPath();
    r.moveTo(x1, y1);
    r.lineTo(x2, y2);
    r.stroke();
  } else if (d.type === "ray") {
    r.setStrokeStyle(theme.drawingRay);
    r.setLineWidth(1.5);
    const dx = x2 - x1 || 1;
    const dy = y2 - y1;
    const scale = layout.plotWidth / Math.abs(dx);
    r.beginPath();
    r.moveTo(x1, y1);
    r.lineTo(x1 + dx * scale, y1 + dy * scale);
    r.stroke();
  } else if (d.type === "rect") {
    r.setStrokeStyle(theme.drawingRect);
    r.setFillStyle("rgba(255,107,0,0.08)");
    const x = Math.min(x1, x2);
    const y = Math.min(y1, y2);
    r.fillRect(x, y, Math.abs(x2 - x1), Math.abs(y2 - y1));
    r.strokeRect(x, y, Math.abs(x2 - x1), Math.abs(y2 - y1));
  } else if (d.type === "fib") {
    const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
    const left = Math.min(x1, x2);
    const right = Math.max(x1, x2);
    for (const lv of levels) {
      const price = d.p1 + (d.p2 - d.p1) * lv;
      const y = priceY(price, layout.mainTop, layout.mainH);
      r.setStrokeStyle(theme.fib);
      r.setGlobalAlpha(0.7);
      r.beginPath();
      r.moveTo(left, y);
      r.lineTo(right, y);
      r.stroke();
      r.setGlobalAlpha(1);
      r.setFillStyle(theme.fib);
      r.setFont(theme.fontSmall);
      r.fillText(`${(lv * 100).toFixed(1)}%`, right + 4, y + 3);
    }
  }
}

export function drawDrawings(ctx: PaintContext): void {
  for (const d of ctx.drawings) paintDrawing(ctx, d);
  if (!ctx.draft) return;
  const d = ctx.draft;
  if (d.type === "hline") return;
  const fake = {
    id: "draft",
    type: d.type === "cursor" ? "trend" : d.type,
    t1: candleTimeSec(ctx.candles[Math.round(d.i1)]?.time ?? ctx.candles[0].time),
    p1: d.p1,
    t2: candleTimeSec(ctx.candles[Math.round(d.i2)]?.time ?? ctx.candles[0].time),
    p2: d.p2,
  } as ChartDrawing;
  paintDrawing(ctx, fake);
}

export type { ChartMarker };
