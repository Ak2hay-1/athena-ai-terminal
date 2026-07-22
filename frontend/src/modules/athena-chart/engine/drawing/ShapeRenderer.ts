import type { DrawingObject } from "../../types";
import type { AthenaChartTheme } from "../../theme";
import type { CoordHelpers } from "./HitTest";
import { getAnchors, pointToScreen } from "./HitTest";
import { formatPriceLabel } from "../../utils/format";
import type { IChartRenderer as Renderer } from "../renderers/types";

const FIB_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];

export interface RenderFrame {
  r: Renderer;
  theme: AthenaChartTheme;
  helpers: CoordHelpers;
  hideHandles?: boolean;
  priceMin: number;
  priceMax: number;
}

function applyStroke(r: Renderer, o: DrawingObject): void {
  r.setStrokeStyle(o.style.color);
  r.setLineWidth(o.style.lineWidth);
  r.setLineDash(o.style.dash);
}

export function renderDrawing(o: DrawingObject, frame: RenderFrame): void {
  if (!o.visible) return;
  const { r, helpers, theme } = frame;
  const screens = o.points.map((p) => pointToScreen(p, helpers));
  const L = helpers.layout;

  switch (o.type) {
    case "hline": {
      const y = screens[0]?.y ?? 0;
      applyStroke(r, o);
      r.beginPath();
      r.moveTo(0, y);
      r.lineTo(L.plotWidth, y);
      r.stroke();
      r.setLineDash([]);
      r.setFillStyle(o.style.color);
      r.setFont(theme.fontSmall);
      r.fillText(formatPriceLabel(o.points[0]?.p ?? 0), L.plotWidth - 52, y - 4);
      break;
    }
    case "vline": {
      const x = screens[0]?.x ?? 0;
      applyStroke(r, o);
      r.beginPath();
      r.moveTo(x, L.mainTop);
      r.lineTo(x, L.plotBottom);
      r.stroke();
      r.setLineDash([]);
      break;
    }
    case "trend":
    case "measure": {
      if (screens.length < 2) break;
      applyStroke(r, o);
      r.beginPath();
      r.moveTo(screens[0].x, screens[0].y);
      r.lineTo(screens[1].x, screens[1].y);
      r.stroke();
      r.setLineDash([]);
      if (o.type === "measure") renderMeasureLabel(o, screens, frame);
      break;
    }
    case "ray": {
      if (screens.length < 2) break;
      applyStroke(r, o);
      const dir = o.meta.rayDirection ?? "right";
      const dx = screens[1].x - screens[0].x || 1;
      const dy = screens[1].y - screens[0].y;
      const scale = L.plotWidth / Math.abs(dx);
      r.beginPath();
      if (dir === "right" || dir === "both") {
        r.moveTo(screens[0].x, screens[0].y);
        r.lineTo(screens[0].x + dx * scale, screens[0].y + dy * scale);
      }
      if (dir === "left" || dir === "both") {
        r.moveTo(screens[0].x, screens[0].y);
        r.lineTo(screens[0].x - dx * scale, screens[0].y - dy * scale);
      }
      r.stroke();
      r.setLineDash([]);
      break;
    }
    case "rect": {
      if (screens.length < 2) break;
      const x = Math.min(screens[0].x, screens[1].x);
      const y = Math.min(screens[0].y, screens[1].y);
      const w = Math.abs(screens[1].x - screens[0].x);
      const h = Math.abs(screens[1].y - screens[0].y);
      const fill = hexToRgba(o.style.color, o.style.fillOpacity);
      r.setFillStyle(fill);
      r.fillRect(x, y, w, h);
      applyStroke(r, o);
      r.strokeRect(x, y, w, h);
      r.setLineDash([]);
      break;
    }
    case "circle": {
      if (screens.length < 2) break;
      const cx = (screens[0].x + screens[1].x) / 2;
      const cy = (screens[0].y + screens[1].y) / 2;
      const rx = Math.abs(screens[1].x - screens[0].x) / 2;
      const ry = Math.abs(screens[1].y - screens[0].y) / 2;
      const c2d = r.getCanvas2D();
      if (c2d) {
        c2d.beginPath();
        c2d.ellipse(cx, cy, Math.max(1, rx), Math.max(1, ry), 0, 0, Math.PI * 2);
        c2d.fillStyle = hexToRgba(o.style.color, o.style.fillOpacity);
        c2d.fill();
        c2d.strokeStyle = o.style.color;
        c2d.lineWidth = o.style.lineWidth;
        c2d.stroke();
      }
      break;
    }
    case "arrow": {
      if (screens.length < 2) break;
      const color =
        o.meta.arrowStyle === "bullish"
          ? theme.bullish
          : o.meta.arrowStyle === "bearish"
            ? theme.bearish
            : o.style.color;
      r.setStrokeStyle(color);
      r.setLineWidth(o.style.lineWidth);
      r.beginPath();
      r.moveTo(screens[0].x, screens[0].y);
      r.lineTo(screens[1].x, screens[1].y);
      r.stroke();
      drawArrowHead(r, screens[0].x, screens[0].y, screens[1].x, screens[1].y, color);
      break;
    }
    case "text": {
      const s = screens[0];
      if (!s) break;
      const text = o.meta.text || "Text";
      const fontStyle = `${o.style.fontItalic ? "italic " : ""}${o.style.fontBold ? "bold " : ""}${o.style.fontSize}px "IBM Plex Sans", sans-serif`;
      r.setFont(fontStyle);
      if (o.style.background) {
        r.setFillStyle(o.style.background);
        r.fillRect(s.x - 4, s.y - o.style.fontSize, text.length * o.style.fontSize * 0.55 + 8, o.style.fontSize + 8);
      }
      r.setFillStyle(o.style.color);
      r.fillText(text, s.x, s.y);
      break;
    }
    case "fib": {
      if (screens.length < 2) break;
      const left = Math.min(screens[0].x, screens[1].x);
      const right = Math.max(screens[0].x, screens[1].x);
      const p1 = o.points[0].p;
      const p2 = o.points[1].p;
      for (const lv of FIB_LEVELS) {
        const price = p1 + (p2 - p1) * lv;
        const y = helpers.priceY(price, L.mainTop, L.mainH);
        r.setStrokeStyle(o.style.color);
        r.setGlobalAlpha(0.75);
        r.beginPath();
        r.moveTo(left, y);
        r.lineTo(right, y);
        r.stroke();
        r.setGlobalAlpha(1);
        r.setFillStyle(o.style.color);
        r.setFont(theme.fontSmall);
        r.fillText(`${(lv * 100).toFixed(1)}%`, right + 4, y + 3);
      }
      break;
    }
  }

  if (o.selected && !frame.hideHandles) {
    for (const a of getAnchors(o, helpers)) {
      r.setFillStyle("#fff");
      r.setStrokeStyle(o.style.color);
      r.setLineWidth(1);
      r.beginPath();
      r.arc(a.x, a.y, 4, 0, Math.PI * 2);
      r.fill();
      r.stroke();
    }
  }
}

function renderMeasureLabel(
  o: DrawingObject,
  screens: Array<{ x: number; y: number }>,
  frame: RenderFrame,
): void {
  if (o.points.length < 2) return;
  const p1 = o.points[0];
  const p2 = o.points[1];
  const dPrice = p2.p - p1.p;
  const pct = p1.p !== 0 ? (dPrice / p1.p) * 100 : 0;
  const bars = Math.abs(
    frame.helpers.indexFromTime(p2.t) - frame.helpers.indexFromTime(p1.t),
  );
  const secs = Math.abs(p2.t - p1.t);
  const pips = Math.abs(dPrice) * (Math.abs(p1.p) > 50 ? 10 : 10000);
  const label = `${dPrice >= 0 ? "+" : ""}${dPrice.toFixed(5)}  ${pct.toFixed(2)}%  ${pips.toFixed(1)}p  ${Math.round(bars)} bars  ${formatDuration(secs)}`;
  const mx = (screens[0].x + screens[1].x) / 2;
  const my = (screens[0].y + screens[1].y) / 2 - 10;
  frame.r.setFillStyle("rgba(0,0,0,0.75)");
  frame.r.fillRect(mx - 4, my - 12, Math.min(320, label.length * 6.2), 16);
  frame.r.setFillStyle("#e8e8e8");
  frame.r.setFont(frame.theme.fontSmall);
  frame.r.fillText(label, mx, my);
}

function formatDuration(secs: number): string {
  if (secs < 60) return `${secs}s`;
  if (secs < 3600) return `${Math.round(secs / 60)}m`;
  if (secs < 86400) return `${(secs / 3600).toFixed(1)}h`;
  return `${(secs / 86400).toFixed(1)}d`;
}

function drawArrowHead(
  r: Renderer,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  color: string,
): void {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const size = 10;
  r.setFillStyle(color);
  r.beginPath();
  r.moveTo(x2, y2);
  r.lineTo(x2 - size * Math.cos(angle - 0.4), y2 - size * Math.sin(angle - 0.4));
  r.lineTo(x2 - size * Math.cos(angle + 0.4), y2 - size * Math.sin(angle + 0.4));
  r.closePath();
  r.fill();
}

function hexToRgba(hex: string, alpha: number): string {
  if (hex.startsWith("rgba")) return hex;
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const n = parseInt(full, 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return `rgba(${r},${g},${b},${alpha})`;
}

export function renderDrawings(
  objects: DrawingObject[],
  frame: RenderFrame,
  preview: DrawingObject | null,
): void {
  const L = frame.helpers.layout;
  // Viewport culling: skip objects whose all points are far outside visible range
  const from = frame.helpers.viewport.from;
  const to = frame.helpers.viewport.to;
  for (const o of objects) {
    if (!o.visible) continue;
    if (o.type !== "hline" && o.points.length) {
      const idxs = o.points.map((p) => frame.helpers.indexFromTime(p.t));
      const minI = Math.min(...idxs);
      const maxI = Math.max(...idxs);
      if (maxI < from - 5 || minI > to + 5) continue;
    }
    // price cull for hline
    if (o.type === "hline") {
      const p = o.points[0]?.p;
      if (p != null && (p < frame.priceMin || p > frame.priceMax)) continue;
    }
    renderDrawing(o, frame);
  }
  if (preview) renderDrawing(preview, { ...frame, hideHandles: true });
  void L;
}
