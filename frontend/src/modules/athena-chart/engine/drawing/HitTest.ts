import type { DrawingObject, DrawingPoint, PaneLayout } from "../../types";
import type { Viewport } from "../viewport";

export interface CoordHelpers {
  viewport: Viewport;
  layout: PaneLayout;
  priceY: (price: number, top: number, h: number) => number;
  yToPrice: (y: number, top: number, h: number) => number;
  indexFromTime: (t: number) => number;
  timeFromIndex: (i: number) => number;
}

export function pointToScreen(
  pt: DrawingPoint,
  h: CoordHelpers,
): { x: number; y: number } {
  const idx = h.indexFromTime(pt.t);
  const x = h.viewport.indexToX(idx + 0.5, h.layout.plotLeft, h.layout.plotWidth);
  const y = h.priceY(pt.p, h.layout.mainTop, h.layout.mainH);
  return { x, y };
}

export function screenToPoint(
  x: number,
  y: number,
  h: CoordHelpers,
): DrawingPoint {
  const idx = h.viewport.xToIndex(x, h.layout.plotLeft, h.layout.plotWidth);
  return {
    t: h.timeFromIndex(idx),
    p: h.yToPrice(y, h.layout.mainTop, h.layout.mainH),
  };
}

export function distPoint(ax: number, ay: number, bx: number, by: number): number {
  return Math.hypot(ax - bx, ay - by);
}

export function distToSegment(
  px: number,
  py: number,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
): number {
  const dx = x2 - x1;
  const dy = y2 - y1;
  if (dx === 0 && dy === 0) return Math.hypot(px - x1, py - y1);
  const t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)));
  return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
}

export interface HitResult {
  object: DrawingObject;
  anchorIndex: number | null;
}

const HANDLE_R = 6;
const LINE_TOL = 6;

export function hitTestDrawings(
  x: number,
  y: number,
  objects: DrawingObject[],
  helpers: CoordHelpers,
): HitResult | null {
  // Top-most first
  const sorted = objects
    .filter((o) => o.visible)
    .slice()
    .sort((a, b) => b.zIndex - a.zIndex);

  for (const o of sorted) {
    const screens = o.points.map((p) => pointToScreen(p, helpers));
    for (let i = 0; i < screens.length; i++) {
      if (distPoint(x, y, screens[i].x, screens[i].y) <= HANDLE_R) {
        return { object: o, anchorIndex: i };
      }
    }
    if (hitShape(o, x, y, screens, helpers)) {
      return { object: o, anchorIndex: null };
    }
  }
  return null;
}

function hitShape(
  o: DrawingObject,
  x: number,
  y: number,
  screens: Array<{ x: number; y: number }>,
  helpers: CoordHelpers,
): boolean {
  const L = helpers.layout;
  switch (o.type) {
    case "hline": {
      const sy = screens[0]?.y ?? 0;
      return Math.abs(y - sy) <= LINE_TOL && x <= L.plotWidth;
    }
    case "vline": {
      const sx = screens[0]?.x ?? 0;
      return Math.abs(x - sx) <= LINE_TOL;
    }
    case "trend":
    case "arrow":
    case "measure":
    case "ray": {
      if (screens.length < 2) return false;
      return distToSegment(x, y, screens[0].x, screens[0].y, screens[1].x, screens[1].y) <= LINE_TOL;
    }
    case "rect":
    case "circle":
    case "fib": {
      if (screens.length < 2) return false;
      const minX = Math.min(screens[0].x, screens[1].x);
      const maxX = Math.max(screens[0].x, screens[1].x);
      const minY = Math.min(screens[0].y, screens[1].y);
      const maxY = Math.max(screens[0].y, screens[1].y);
      const pad = LINE_TOL;
      return x >= minX - pad && x <= maxX + pad && y >= minY - pad && y <= maxY + pad;
    }
    case "text": {
      const s = screens[0];
      if (!s) return false;
      return distPoint(x, y, s.x, s.y) <= 20;
    }
    default:
      return false;
  }
}

export function getAnchors(
  o: DrawingObject,
  helpers: CoordHelpers,
): Array<{ x: number; y: number; index: number }> {
  return o.points.map((p, index) => {
    const s = pointToScreen(p, helpers);
    return { ...s, index };
  });
}
