import type {
  Candlestick,
  DrawingObject,
  DrawingTool,
  DrawingType,
  MagnetMode,
  PaneLayout,
} from "../../types";
import type { AthenaChartTheme } from "../../theme";
import { candleTimeSec } from "../../utils/format";
import type { IChartRenderer } from "../renderers/types";
import type { Viewport } from "../viewport";
import { DrawingManager } from "./DrawingManager";
import { createDrawingObject } from "./factory";
import { hitTestDrawings, screenToPoint, type CoordHelpers } from "./HitTest";
import { snapPriceAdvanced } from "./magnet";
import { renderDrawings, type RenderFrame } from "./ShapeRenderer";

export interface DrawingEngineHost {
  getCandles: () => Candlestick[];
  getViewport: () => Viewport;
  getLayout: () => PaneLayout;
  priceY: (price: number, top: number, h: number) => number;
  yToPrice: (y: number, top: number, h: number) => number;
  getPriceMin: () => number;
  getPriceMax: () => number;
  markDirty: () => void;
  panByDeltaX?: (dx: number, plotWidth: number) => void;
  zoomAt?: (anchorIndex: number, factor: number) => void;
}

const CREATE_TOOLS: DrawingType[] = [
  "trend",
  "hline",
  "vline",
  "ray",
  "rect",
  "circle",
  "arrow",
  "text",
  "fib",
  "measure",
];

/**
 * DrawingEngine — owns tool sessions, selection, preview.
 * No React. ChartController delegates pointer events here.
 */
export class DrawingEngine {
  readonly manager = new DrawingManager();
  private tool: DrawingTool = "crosshair";
  private magnetMode: MagnetMode = "strong";
  private preview: DrawingObject | null = null;
  private creating = false;
  private startPoint: { t: number; p: number } | null = null;
  private dragMode: "none" | "pan" | "move" | "anchor" | "create" = "none";
  private dragAnchor: number | null = null;
  private dragLastX = 0;
  private dragLastY = 0;
  private moveBefore: DrawingObject[] = [];
  private host: DrawingEngineHost;
  private hideChrome = false;

  onContextMenu?: (x: number, y: number, drawingId: string | null) => void;
  onTextEdit?: (id: string, text: string, screen: { x: number; y: number }) => void;
  onSelectionChange?: (ids: string[]) => void;

  constructor(host: DrawingEngineHost) {
    this.host = host;
  }

  setTool(tool: DrawingTool): void {
    this.tool = tool;
    if (tool !== "cursor" && tool !== "erase") {
      this.manager.clearSelection();
      this.notifySelection();
    }
    this.preview = null;
    this.creating = false;
  }

  getTool(): DrawingTool {
    return this.tool;
  }

  setMagnetMode(mode: MagnetMode): void {
    this.magnetMode = mode;
  }

  setHideChrome(v: boolean): void {
    this.hideChrome = v;
  }

  setObjects(objects: DrawingObject[]): void {
    this.manager.setAll(objects, false);
  }

  private helpers(): CoordHelpers {
    const candles = this.host.getCandles();
    const viewport = this.host.getViewport();
    const layout = this.host.getLayout();
    return {
      viewport,
      layout,
      priceY: this.host.priceY,
      yToPrice: this.host.yToPrice,
      indexFromTime: (t) => {
        if (!candles.length) return 0;
        let best = 0;
        let dist = Infinity;
        for (let i = 0; i < candles.length; i++) {
          const d = Math.abs(candleTimeSec(candles[i].time) - t);
          if (d < dist) {
            dist = d;
            best = i;
          }
        }
        return best;
      },
      timeFromIndex: (i) => {
        if (!candles.length) return Math.floor(Date.now() / 1000);
        const idx = Math.max(0, Math.min(candles.length - 1, Math.round(i)));
        return candleTimeSec(candles[idx].time);
      },
    };
  }

  private snap(index: number, price: number): number {
    return snapPriceAdvanced(this.host.getCandles(), index, price, this.magnetMode);
  }

  private pointAt(x: number, y: number) {
    const h = this.helpers();
    const raw = screenToPoint(x, y, h);
    const idx = h.viewport.xToIndex(x, h.layout.plotLeft, h.layout.plotWidth);
    return { t: raw.t, p: this.snap(idx, raw.p), index: idx };
  }

  handlePointerDown(e: {
    x: number;
    y: number;
    button: number;
    pointerId: number;
  }): boolean {
    if (this.host.getCandles().length === 0) return false;
    const h = this.helpers();
    if (e.x > h.layout.plotWidth) return false;

    if (e.button === 2) {
      const hit = hitTestDrawings(e.x, e.y, this.manager.getAll(), h);
      if (hit) {
        this.manager.select([hit.object.id]);
        this.notifySelection();
      }
      this.onContextMenu?.(e.x, e.y, hit?.object.id ?? null);
      this.host.markDirty();
      return true;
    }

    if (this.tool === "hand" || this.tool === "crosshair" || this.tool === "zoom") {
      this.dragMode = "pan";
      this.dragLastX = e.x;
      return false; // controller also pans
    }

    if (this.tool === "erase") {
      const hit = hitTestDrawings(e.x, e.y, this.manager.getAll(), h);
      if (hit && !hit.object.locked) {
        this.manager.remove([hit.object.id]);
        this.host.markDirty();
      }
      return true;
    }

    if (this.tool === "cursor") {
      const hit = hitTestDrawings(e.x, e.y, this.manager.getAll(), h);
      if (hit) {
        this.manager.select([hit.object.id]);
        this.notifySelection();
        if (!hit.object.locked) {
          this.moveBefore = this.manager.getSelected().map((o) => ({
            ...o,
            points: o.points.map((p) => ({ ...p })),
            style: { ...o.style },
            meta: { ...o.meta },
          }));
          this.dragMode = hit.anchorIndex != null ? "anchor" : "move";
          this.dragAnchor = hit.anchorIndex;
          this.dragLastX = e.x;
          this.dragLastY = e.y;
        }
        this.host.markDirty();
        return true;
      }
      this.manager.clearSelection();
      this.notifySelection();
      this.dragMode = "pan";
      this.dragLastX = e.x;
      this.host.markDirty();
      return false;
    }

    if (CREATE_TOOLS.includes(this.tool as DrawingType)) {
      const pt = this.pointAt(e.x, e.y);
      if (this.tool === "hline") {
        const obj = createDrawingObject("hline", [{ t: pt.t, p: pt.p }]);
        this.manager.add(obj);
        this.host.markDirty();
        return true;
      }
      if (this.tool === "vline") {
        const obj = createDrawingObject("vline", [{ t: pt.t, p: pt.p }]);
        this.manager.add(obj);
        this.host.markDirty();
        return true;
      }
      if (this.tool === "text") {
        const obj = createDrawingObject(
          "text",
          [{ t: pt.t, p: pt.p }],
          { meta: { text: "Text" } },
        );
        this.manager.add(obj);
        this.onTextEdit?.(obj.id, "Text", { x: e.x, y: e.y });
        this.host.markDirty();
        return true;
      }
      this.creating = true;
      this.dragMode = "create";
      this.startPoint = { t: pt.t, p: pt.p };
      const type = this.tool as DrawingType;
      const meta =
        type === "ray"
          ? { rayDirection: "right" as const }
          : type === "arrow"
            ? { arrowStyle: "neutral" as const }
            : type === "rect"
              ? { zoneKind: "custom" as const }
              : {};
      this.preview = createDrawingObject(
        type,
        [
          { t: pt.t, p: pt.p },
          { t: pt.t, p: pt.p },
        ],
        { meta },
      );
      this.host.markDirty();
      return true;
    }

    return false;
  }

  handlePointerMove(e: { x: number; y: number }): boolean {
    if (this.dragMode === "create" && this.preview && this.startPoint) {
      const pt = this.pointAt(e.x, e.y);
      this.preview = {
        ...this.preview,
        points: [
          { t: this.startPoint.t, p: this.startPoint.p },
          { t: pt.t, p: pt.p },
        ],
        updatedAt: Date.now(),
      };
      this.host.markDirty();
      return true;
    }

    if (this.dragMode === "move" || this.dragMode === "anchor") {
      const h = this.helpers();
      const dx = e.x - this.dragLastX;
      const dy = e.y - this.dragLastY;
      this.dragLastX = e.x;
      this.dragLastY = e.y;
      const selected = this.manager.getSelected();
      const dPrice =
        this.host.yToPrice(0, h.layout.mainTop, h.layout.mainH) -
        this.host.yToPrice(dy, h.layout.mainTop, h.layout.mainH);
      const dIndex = (dx / Math.max(1, h.layout.plotWidth)) * h.viewport.span;

      const updated = selected.map((o) => {
        if (o.locked) return o;
        if (this.dragMode === "anchor" && this.dragAnchor != null) {
          const points = o.points.map((p, i) => {
            if (i !== this.dragAnchor) return p;
            const pt = this.pointAt(e.x, e.y);
            return { t: pt.t, p: pt.p };
          });
          return { ...o, points, updatedAt: Date.now() };
        }
        const points = o.points.map((p) => {
          if (o.type === "hline") return { t: p.t, p: p.p + dPrice };
          if (o.type === "vline") {
            const idx = h.indexFromTime(p.t) + dIndex;
            return { t: h.timeFromIndex(idx), p: p.p };
          }
          const idx = h.indexFromTime(p.t) + dIndex;
          return { t: h.timeFromIndex(idx), p: p.p + dPrice };
        });
        return { ...o, points, updatedAt: Date.now() };
      });
      // live update without history until pointer up
      this.manager.setAll(
        this.manager.getAll().map((o) => updated.find((u) => u.id === o.id) ?? o),
        false,
      );
      this.host.markDirty();
      return true;
    }

    return false;
  }

  handlePointerUp(): boolean {
    if (this.dragMode === "create" && this.preview) {
      const obj = { ...this.preview, selected: false };
      this.manager.add(obj);
      this.preview = null;
      this.creating = false;
      this.dragMode = "none";
      this.startPoint = null;
      this.host.markDirty();
      return true;
    }

    if ((this.dragMode === "move" || this.dragMode === "anchor") && this.moveBefore.length) {
      const after = this.manager.getSelected().map((o) => ({
        ...o,
        points: o.points.map((p) => ({ ...p })),
        style: { ...o.style },
        meta: { ...o.meta },
      }));
      // Record history as update
      this.manager.history.push({
        kind: "update",
        before: this.moveBefore,
        after,
      });
      this.moveBefore = [];
      this.dragMode = "none";
      this.dragAnchor = null;
      this.host.markDirty();
      return true;
    }

    this.dragMode = "none";
    this.creating = false;
    return false;
  }

  cancel(): void {
    this.preview = null;
    this.creating = false;
    this.dragMode = "none";
    this.manager.clearSelection();
    this.notifySelection();
    this.host.markDirty();
  }

  render(
    r: IChartRenderer,
    theme: AthenaChartTheme,
  ): void {
    const frame: RenderFrame = {
      r,
      theme,
      helpers: this.helpers(),
      hideHandles: this.hideChrome,
      priceMin: this.host.getPriceMin(),
      priceMax: this.host.getPriceMax(),
    };
    renderDrawings(this.manager.getVisibleSorted(), frame, this.preview);
  }

  private notifySelection(): void {
    this.onSelectionChange?.(this.manager.getSelected().map((o) => o.id));
  }
}
