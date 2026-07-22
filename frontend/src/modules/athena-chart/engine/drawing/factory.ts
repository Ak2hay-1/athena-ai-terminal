import type {
  ChartDrawing,
  DrawingObject,
  DrawingPoint,
  DrawingStyle,
  DrawingType,
} from "../../types";
import { DEFAULT_DRAWING_STYLE } from "../../types";
import { uid } from "../../utils/uid";

export function createDrawingObject(
  type: DrawingType,
  points: DrawingPoint[],
  partial?: Partial<DrawingObject>,
): DrawingObject {
  const now = Date.now();
  return {
    id: partial?.id ?? uid("d-"),
    type,
    points,
    style: { ...DEFAULT_DRAWING_STYLE, ...(partial?.style ?? {}) },
    layer: partial?.layer ?? "drawings",
    zIndex: partial?.zIndex ?? now,
    locked: partial?.locked ?? false,
    visible: partial?.visible ?? true,
    selected: partial?.selected ?? false,
    meta: partial?.meta ?? {},
    createdAt: partial?.createdAt ?? now,
    updatedAt: now,
  };
}

function isDrawingObject(d: ChartDrawing | DrawingObject): d is DrawingObject {
  return "points" in d && Array.isArray((d as DrawingObject).points);
}

/** Migrate legacy ChartDrawing → DrawingObject. */
export function legacyToObject(d: ChartDrawing | DrawingObject): DrawingObject {
  if (isDrawingObject(d)) return d;
  if (d.type === "hline") {
    return createDrawingObject("hline", [{ t: 0, p: d.price }], { id: d.id });
  }
  return createDrawingObject(
    d.type,
    [
      { t: d.t1, p: d.p1 },
      { t: d.t2, p: d.p2 },
    ],
    {
      id: d.id,
      meta: d.type === "ray" ? { rayDirection: "right" } : {},
    },
  );
}

export function objectToLegacy(o: DrawingObject): ChartDrawing {
  if (o.type === "hline") {
    return { id: o.id, type: "hline", price: o.points[0]?.p ?? 0 };
  }
  if (o.type === "trend" || o.type === "ray" || o.type === "rect" || o.type === "fib") {
    return {
      id: o.id,
      type: o.type,
      t1: o.points[0]?.t ?? 0,
      p1: o.points[0]?.p ?? 0,
      t2: o.points[1]?.t ?? 0,
      p2: o.points[1]?.p ?? 0,
    };
  }
  // Non-legacy types: map to trend segment for Markets callback compatibility
  return {
    id: o.id,
    type: "trend",
    t1: o.points[0]?.t ?? 0,
    p1: o.points[0]?.p ?? 0,
    t2: o.points[1]?.t ?? o.points[0]?.t ?? 0,
    p2: o.points[1]?.p ?? o.points[0]?.p ?? 0,
  };
}

export function cloneStyle(s: DrawingStyle): DrawingStyle {
  return { ...s, dash: [...s.dash] };
}

export function cloneObject(o: DrawingObject): DrawingObject {
  return {
    ...o,
    points: o.points.map((p) => ({ ...p })),
    style: cloneStyle(o.style),
    meta: { ...o.meta },
  };
}
