import type {
  Candlestick,
  ChartDrawing,
  ChartLevels,
  ChartMarker,
  ChartType,
  CrosshairState,
  DrawingObject,
  DrawingTool,
  EngineOptions,
  IndicatorFlags,
  MagnetMode,
  SmartCursorInfo,
} from "../types";
import { DEFAULT_INDICATORS } from "../types";
import { ATHENA_CHART_THEME } from "../theme";
import { candleTimeSec } from "../utils/format";
import { bucketStartUtcMs, utcMsFromIso } from "./time/bucket";
import { DrawingEngine } from "./drawing/DrawingEngine";
import { legacyToObject, objectToLegacy } from "./drawing/factory";
import { computeAtr, computeEma, computeRsi, IndicatorManager } from "./indicators";
import { drawAxes, drawLastPrice } from "./layers/axes";
import { drawCandles } from "./layers/candles";
import type { PaintContext } from "./layers/context";
import { PAD_TOP } from "./layers/context";
import { drawCrosshair } from "./layers/crosshair";
import { drawGrid } from "./layers/grid";
import { computeLayout } from "./layers/layout";
import { drawMarkers } from "./layers/markers";
import {
  drawLevels,
  drawMacdPane,
  drawOverlays,
  drawRsiPane,
} from "./layers/overlays";
import { drawSessions } from "./layers/sessions";
import { drawVolume } from "./layers/volume";
import { createCanvasRenderer } from "./renderers/canvas";
import type { IChartRenderer } from "./renderers/types";
import { Viewport } from "./viewport";
import { renderIntelligenceOverlays } from "../intelligence/overlays/renderer";
import type { AnalysisSnapshot, OverlayVisibility } from "../intelligence/types";
import { DEFAULT_OVERLAYS } from "../intelligence/types";
import { renderDecisionOverlays } from "../decision-engine/overlays/renderer";
import type {
  DecisionOverlayVisibility,
  DecisionSnapshot,
} from "../decision-engine/types";
import { DEFAULT_DECISION_OVERLAYS } from "../decision-engine/types";

/**
 * Framework-agnostic chart controller.
 * Delegates drawings to DrawingEngine; paints candles/indicators/sessions.
 */
export class ChartController {
  private renderer: IChartRenderer;
  private canvasEl: HTMLCanvasElement;
  private ro: ResizeObserver | null = null;
  private raf = 0;
  private dirty = true;

  private candles: Candlestick[] = [];
  private viewport = new Viewport();
  private fitted = false;
  private prevFirstTime: string | null = null;
  private prevLen = 0;
  private prevSeriesId = "";
  private liveMode = true;

  private width = 0;
  private height = 0;
  private dpr = 1;

  private mode: "advanced" | "overview" = "advanced";
  private chartType: ChartType = "candles";
  private indicators: IndicatorFlags = { ...DEFAULT_INDICATORS };
  private levels: ChartLevels | null = null;
  private markers: ChartMarker[] = [];
  private tool: DrawingTool = "crosshair";
  private magnetMode: MagnetMode = "strong";
  private showSessions = false;
  private sessionFlags: Record<string, boolean> = {
    sydney: true,
    tokyo: true,
    london: true,
    newyork: true,
  };
  private hideChrome = false;
  private intelligenceSnapshot: AnalysisSnapshot | null = null;
  private intelligenceOverlays: OverlayVisibility = { ...DEFAULT_OVERLAYS };
  private decisionSnapshot: DecisionSnapshot | null = null;
  private decisionOverlays: DecisionOverlayVisibility = {
    ...DEFAULT_DECISION_OVERLAYS,
  };

  private onNeedMoreHistory?: () => void;
  private historyThreshold = 50;
  private isLoadingHistory = false;
  private onDrawingComplete?: (d: ChartDrawing) => void;
  private onCrosshair?: EngineOptions["onCrosshair"];
  private onFps?: (fps: number) => void;
  private onViewportChange?: EngineOptions["onViewportChange"];
  private onHistoryChange?: EngineOptions["onHistoryChange"];

  readonly drawingEngine: DrawingEngine;
  readonly indicatorManager = new IndicatorManager();

  private crosshair: CrosshairState = {
    x: 0,
    y: 0,
    barIndex: 0,
    price: 0,
    visible: false,
  };

  private priceMin = 0;
  private priceMax = 1;
  private targetPriceMin = 0;
  private targetPriceMax = 1;
  private priceScaleInitialized = false;

  private dragging = false;
  private dragLastX = 0;
  private paneDrag: "rsi" | "macd" | null = null;
  private rsiFrac = 0.18;
  private macdFrac = 0.18;

  private frames = 0;
  private fpsLast = performance.now();
  private fps = 0;

  private priceY = (price: number, top: number, h: number) => {
    const span = Math.max(1e-12, this.priceMax - this.priceMin);
    return top + ((this.priceMax - price) / span) * h;
  };

  private yToPrice = (y: number, top: number, h: number) => {
    const span = Math.max(1e-12, this.priceMax - this.priceMin);
    return this.priceMax - ((y - top) / Math.max(1, h)) * span;
  };

  constructor(canvas: HTMLCanvasElement, options: EngineOptions = {}) {
    this.canvasEl = canvas;
    this.renderer = createCanvasRenderer(canvas);
    this.drawingEngine = new DrawingEngine({
      getCandles: () => this.candles,
      getViewport: () => this.viewport,
      getLayout: () => this.layout(),
      priceY: this.priceY,
      yToPrice: this.yToPrice,
      getPriceMin: () => this.priceMin,
      getPriceMax: () => this.priceMax,
      markDirty: () => {
        this.dirty = true;
      },
    });
    this.drawingEngine.manager.setCallbacks({
      onChange: (objs) => {
        options.onDrawingsChange?.(objs);
        if (this.onDrawingComplete && objs.length) {
          // Markets compat: emit last as legacy on external sync only when needed
        }
      },
      onHistory: (u, r) => this.onHistoryChange?.(u, r),
    });
    this.applyOptions(options);
    this.bind();
    this.schedule();
  }

  applyOptions(options: EngineOptions): void {
    if (options.mode) this.mode = options.mode;
    if (options.chartType) this.chartType = options.chartType;
    if (options.indicators) this.indicators = options.indicators;
    if (options.levels !== undefined) this.levels = options.levels;
    if (options.markers) this.markers = options.markers;
    if (options.drawingObjects) {
      this.drawingEngine.setObjects(options.drawingObjects);
    } else if (options.drawings) {
      this.drawingEngine.setObjects(options.drawings.map(legacyToObject));
    }
    if (options.tool) {
      this.tool = options.tool;
      this.drawingEngine.setTool(options.tool);
    }
    if (options.magnetMode) {
      this.magnetMode = options.magnetMode;
      this.drawingEngine.setMagnetMode(options.magnetMode);
    } else if (options.magnet != null) {
      this.magnetMode = options.magnet ? "strong" : "off";
      this.drawingEngine.setMagnetMode(this.magnetMode);
    }
    if (options.showSessions != null) this.showSessions = options.showSessions;
    if (options.sessionFlags) this.sessionFlags = options.sessionFlags;
    if (options.hideChrome != null) {
      this.hideChrome = options.hideChrome;
      this.drawingEngine.setHideChrome(options.hideChrome);
    }
    if (options.intelligenceSnapshot !== undefined) {
      this.intelligenceSnapshot = options.intelligenceSnapshot;
    }
    if (options.intelligenceOverlays) {
      this.intelligenceOverlays = options.intelligenceOverlays;
    }
    if (options.decisionSnapshot !== undefined) {
      this.decisionSnapshot = options.decisionSnapshot;
    }
    if (options.decisionOverlays) {
      this.decisionOverlays = options.decisionOverlays;
    }
    if (options.onNeedMoreHistory !== undefined) {
      this.onNeedMoreHistory = options.onNeedMoreHistory;
    }
    if (options.historyThreshold != null) {
      this.historyThreshold = options.historyThreshold;
    }
    if (options.isLoadingHistory != null) {
      this.isLoadingHistory = options.isLoadingHistory;
    }
    if (options.onDrawingComplete) this.onDrawingComplete = options.onDrawingComplete;
    if (options.onDrawingsChange) {
      this.drawingEngine.manager.setCallbacks({
        onChange: options.onDrawingsChange,
        onHistory: (u, r) => this.onHistoryChange?.(u, r),
      });
    }
    if (options.onSelectionChange) {
      this.drawingEngine.onSelectionChange = options.onSelectionChange;
    }
    if (options.onContextMenu) {
      this.drawingEngine.onContextMenu = (x, y, id) =>
        options.onContextMenu?.({ x, y, drawingId: id });
    }
    if (options.onTextEdit) {
      this.drawingEngine.onTextEdit = options.onTextEdit;
    }
    if (options.onCrosshair) this.onCrosshair = options.onCrosshair;
    if (options.onFps) this.onFps = options.onFps;
    if (options.onViewportChange) this.onViewportChange = options.onViewportChange;
    if (options.onHistoryChange) this.onHistoryChange = options.onHistoryChange;
    this.dirty = true;
  }

  getDrawingObjects(): DrawingObject[] {
    return this.drawingEngine.manager.getAll();
  }

  undo(): void {
    this.drawingEngine.manager.undo();
    this.dirty = true;
  }

  redo(): void {
    this.drawingEngine.manager.redo();
    this.dirty = true;
  }

  setCandles(candles: Candlestick[]): void {
    const first = candles[0]?.time ?? null;
    const prepended =
      this.prevFirstTime != null &&
      first != null &&
      first !== this.prevFirstTime &&
      candles.length > this.prevLen
        ? candles.length - this.prevLen
        : 0;

    if (prepended > 0) {
      this.viewport.set(
        this.viewport.from + prepended,
        this.viewport.to + prepended,
        candles.length,
      );
    }

    this.candles = candles;
    const seriesId = candles[0]
      ? `${candles[0].symbol}:${candles[0].timeframe}`
      : "";
    if (seriesId && seriesId !== this.prevSeriesId) {
      this.priceScaleInitialized = false;
      this.prevSeriesId = seriesId;
      this.fitted = false;
    }
    if (!this.fitted && candles.length > 0) {
      this.viewport.fit(candles.length, this.mode === "overview" ? candles.length : 140);
      this.fitted = true;
    } else if (candles.length > 0) {
      if (this.liveMode) {
        const span = Math.max(20, this.viewport.span);
        this.viewport.set(candles.length - span, candles.length, candles.length);
      } else {
        this.viewport.set(this.viewport.from, this.viewport.to, candles.length);
      }
    }

    this.prevFirstTime = first;
    this.prevLen = candles.length;
    this.dirty = true;
    this.emitCrosshair();
    this.onViewportChange?.(this.viewport.clone());
  }

  updateLive(candle: Candlestick): void {
    if (this.candles.length === 0) {
      this.setCandles([candle]);
      return;
    }
    const last = this.candles[this.candles.length - 1];
    const tf = (candle.timeframe || last.timeframe || "M5").toUpperCase();
    let liveBucket: number;
    let lastBucket: number;
    try {
      liveBucket = bucketStartUtcMs(utcMsFromIso(candle.time), tf);
      lastBucket = bucketStartUtcMs(utcMsFromIso(last.time), tf);
    } catch {
      // Unknown TF — fall back to second equality
      const liveTs = candleTimeSec(candle.time);
      const lastTs = candleTimeSec(last.time);
      if (liveTs < lastTs) return;
      const next = [...this.candles];
      if (liveTs === lastTs) next[next.length - 1] = candle;
      else next.push(candle);
      this.candles = next;
      this.prevLen = next.length;
      this.dirty = true;
      return;
    }

    // Stale tick for an older bucket — ignore (never stretch overnight bars)
    if (liveBucket < lastBucket) return;

    const next = [...this.candles];
    if (liveBucket === lastBucket) {
      next[next.length - 1] = candle;
    } else {
      // Newer bucket — append only; gap fill is the data layer's job
      next.push(candle);
    }
    this.candles = next;
    this.prevLen = next.length;
    if (this.liveMode && liveBucket > lastBucket) {
      const span = Math.max(20, this.viewport.span);
      this.viewport.set(next.length - span, next.length, next.length);
      this.onViewportChange?.(this.viewport.clone());
    }
    this.dirty = true;
  }

  /** Snap viewport to the latest bars and keep following. */
  goLive(): void {
    this.liveMode = true;
    const len = this.candles.length;
    if (len > 0) {
      const span = Math.max(20, Math.min(140, this.viewport.span || 140));
      this.viewport.set(len - span, len, len);
      this.onViewportChange?.(this.viewport.clone());
    }
    this.dirty = true;
  }

  setLiveMode(on: boolean): void {
    this.liveMode = on;
    if (on) this.goLive();
  }

  isLiveMode(): boolean {
    return this.liveMode;
  }

  /** Restore a saved viewport range without fitting. */
  restoreViewport(from: number, to: number, total: number): void {
    this.liveMode = false;
    this.fitted = true;
    this.viewport.set(from, to, total);
    this.onViewportChange?.(this.viewport.clone());
    this.dirty = true;
  }

  fitContent(): void {
    this.viewport.fit(this.candles.length, this.mode === "overview" ? this.candles.length : 140);
    this.dirty = true;
    this.onViewportChange?.(this.viewport.clone());
  }

  zoomPreset(bars: number | null): void {
    if (bars == null) {
      this.fitContent();
      return;
    }
    const len = this.candles.length;
    const span = Math.min(len, Math.max(20, bars));
    this.viewport.set(len - span, len, len);
    this.dirty = true;
    this.onViewportChange?.(this.viewport.clone());
  }

  exportPng(opts?: { hideChrome?: boolean }): string {
    const prev = this.hideChrome;
    if (opts?.hideChrome) {
      this.hideChrome = true;
      this.drawingEngine.setHideChrome(true);
    }
    this.paint();
    const url = this.renderer.toDataURL?.("image/png") ?? "";
    this.hideChrome = prev;
    this.drawingEngine.setHideChrome(prev);
    this.dirty = true;
    return url;
  }

  getFps(): number {
    return this.fps;
  }

  destroy(): void {
    cancelAnimationFrame(this.raf);
    this.ro?.disconnect();
    this.canvasEl.removeEventListener("pointerdown", this.onPointerDown);
    this.canvasEl.removeEventListener("pointermove", this.onPointerMove);
    this.canvasEl.removeEventListener("pointerup", this.onPointerUp);
    this.canvasEl.removeEventListener("pointerleave", this.onPointerLeave);
    this.canvasEl.removeEventListener("wheel", this.onWheel);
    this.canvasEl.removeEventListener("contextmenu", this.onContextMenu);
    window.removeEventListener("keydown", this.onKeyDown);
  }

  private bind(): void {
    this.ro = new ResizeObserver(() => this.resize());
    this.ro.observe(this.canvasEl.parentElement ?? this.canvasEl);
    this.canvasEl.addEventListener("pointerdown", this.onPointerDown);
    this.canvasEl.addEventListener("pointermove", this.onPointerMove);
    this.canvasEl.addEventListener("pointerup", this.onPointerUp);
    this.canvasEl.addEventListener("pointerleave", this.onPointerLeave);
    this.canvasEl.addEventListener("wheel", this.onWheel, { passive: false });
    this.canvasEl.addEventListener("contextmenu", this.onContextMenu);
    window.addEventListener("keydown", this.onKeyDown);
    this.resize();
  }

  private onContextMenu = (e: Event): void => {
    e.preventDefault();
  };

  private resize = (): void => {
    const parent = this.canvasEl.parentElement ?? this.canvasEl;
    const w = parent.clientWidth || 600;
    const h = parent.clientHeight || 400;
    this.dpr = Math.min(2, window.devicePixelRatio || 1);
    this.width = w;
    this.height = h;
    this.renderer.resize(w, h, this.dpr);
    this.dirty = true;
  };

  private schedule = (): void => {
    this.raf = requestAnimationFrame(() => {
      this.frames += 1;
      const now = performance.now();
      if (now - this.fpsLast >= 1000) {
        this.fps = this.frames;
        this.frames = 0;
        this.fpsLast = now;
        this.onFps?.(this.fps);
      }
      if (this.dirty) {
        this.paint();
        this.dirty = false;
      }
      this.schedule();
    });
  };

  private layout() {
    return computeLayout(
      this.width,
      this.height,
      this.mode,
      this.indicators,
      this.rsiFrac,
      this.macdFrac,
    );
  }

  private computePriceRange(start: number, end: number): void {
    let min = Infinity;
    let max = -Infinity;
    for (let i = start; i < end; i++) {
      const c = this.candles[i];
      if (!c) continue;
      min = Math.min(min, c.low);
      max = Math.max(max, c.high);
    }
    if (!Number.isFinite(min) || !Number.isFinite(max)) {
      min = 0;
      max = 1;
    }
    const pad = (max - min) * 0.06 || max * 0.01 || 1;
    this.targetPriceMin = min - pad;
    this.targetPriceMax = max + pad * (this.indicators.volume ? 1.25 : 1);

    if (!this.priceScaleInitialized) {
      this.priceMin = this.targetPriceMin;
      this.priceMax = this.targetPriceMax;
      this.priceScaleInitialized = true;
      return;
    }

    // Smooth lerp toward target — avoid sudden jumps
    const alpha = 0.18;
    this.priceMin += (this.targetPriceMin - this.priceMin) * alpha;
    this.priceMax += (this.targetPriceMax - this.priceMax) * alpha;

    // Keep animating while scale is settling
    if (
      Math.abs(this.targetPriceMin - this.priceMin) > 1e-10 ||
      Math.abs(this.targetPriceMax - this.priceMax) > 1e-10
    ) {
      this.dirty = true;
    }
  }

  private buildPaintContext(layout: ReturnType<ChartController["layout"]>): PaintContext {
    return {
      r: this.renderer,
      theme: ATHENA_CHART_THEME,
      viewport: this.viewport,
      width: this.width,
      height: this.height,
      candles: this.candles,
      chartType: this.chartType,
      indicators: this.indicators,
      levels: this.levels,
      markers: this.markers,
      drawings: this.drawingEngine.manager.getAll().map(objectToLegacy),
      draft: null,
      crosshair: this.crosshair,
      priceMin: this.priceMin,
      priceMax: this.priceMax,
      mode: this.mode,
      layout,
      priceY: this.priceY,
      symbol: this.candles[0]?.symbol,
    };
  }

  private paint(): void {
    const theme = ATHENA_CHART_THEME;
    this.renderer.clear(theme.background);

    if (this.candles.length === 0) {
      this.renderer.setFillStyle(theme.text);
      this.renderer.setFont(theme.font);
      this.renderer.fillText("No candle data", 16, 32);
      return;
    }

    const L = this.layout();
    const { start, end } = this.viewport.visibleRange(this.candles.length);
    this.computePriceRange(start, end);
    const ctx = this.buildPaintContext(L);

    drawGrid(ctx);
    if (this.showSessions && this.mode === "advanced") {
      drawSessions(ctx, this.sessionFlags);
    }
    drawVolume(ctx, start, end);
    drawCandles(ctx, start, end);
    drawOverlays(ctx, start, end);
    this.indicatorManager.renderAll({
      r: this.renderer,
      candles: this.candles,
      viewport: this.viewport,
      layout: L,
      priceY: this.priceY,
      start,
      end,
    });
    // AI / Intelligence overlay layer
    if (this.mode === "advanced" && this.intelligenceSnapshot) {
      renderIntelligenceOverlays({
        r: this.renderer,
        theme,
        viewport: this.viewport,
        layout: L,
        priceY: this.priceY,
        indexFromTime: (t) => {
          const target = candleTimeSec(t);
          let best = 0;
          let dist = Infinity;
          for (let i = 0; i < this.candles.length; i++) {
            const d = Math.abs(candleTimeSec(this.candles[i].time) - target);
            if (d < dist) {
              dist = d;
              best = i;
            }
          }
          return best;
        },
        overlays: this.intelligenceOverlays,
        snapshot: this.intelligenceSnapshot,
      });
    }
    if (this.mode === "advanced" && this.decisionSnapshot) {
      renderDecisionOverlays({
        r: this.renderer,
        theme,
        viewport: this.viewport,
        layout: L,
        priceY: this.priceY,
        overlays: this.decisionOverlays,
        snapshot: this.decisionSnapshot,
      });
    }
    drawLevels(ctx);
    drawMarkers(ctx);
    // Drawings layer
    if (this.mode === "advanced") {
      this.drawingEngine.render(this.renderer, theme);
    }
    if (L.showRsi) drawRsiPane(ctx, start, end);
    if (L.showMacd) drawMacdPane(ctx, start, end);
    drawAxes(ctx, start, end);
    if (this.indicators.priceLine) drawLastPrice(ctx);
    if (!this.hideChrome) drawCrosshair(ctx);
  }

  private buildSmartCursor(idx: number): SmartCursorInfo | null {
    const c = this.candles[idx];
    if (!c) return null;
    const prev = this.candles[idx - 1];
    const atrArr = computeAtr(this.candles);
    return {
      price: this.crosshair.price,
      timeSec: candleTimeSec(c.time),
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
      volume: c.tick_volume,
      pctChange: prev ? ((c.close - prev.close) / prev.close) * 100 : null,
      spread: null,
      atr: atrArr[idx] ?? null,
    };
  }

  private emitCrosshair(): void {
    if (!this.onCrosshair) return;
    if (!this.crosshair.visible || this.candles.length === 0) {
      const last = this.candles.length - 1;
      this.onCrosshair(
        this.candles.at(-1) ?? null,
        this.legendExtras(last),
        this.buildSmartCursor(last),
      );
      return;
    }
    const idx = Math.max(
      0,
      Math.min(this.candles.length - 1, Math.round(this.crosshair.barIndex)),
    );
    this.onCrosshair(
      this.candles[idx] ?? null,
      this.legendExtras(idx),
      this.buildSmartCursor(idx),
    );
  }

  private legendExtras(
    idx: number,
  ): Array<{ label: string; value: string; color?: string }> {
    if (idx < 0 || !this.candles[idx]) return [];
    const closes = this.candles.map((c) => c.close);
    const extras: Array<{ label: string; value: string; color?: string }> = [];
    const T = ATHENA_CHART_THEME;
    if (this.indicators.ema20) {
      const v = computeEma(closes, 20)[idx];
      if (v != null) extras.push({ label: "EMA20", value: v.toFixed(5), color: T.ema20 });
    }
    if (this.indicators.rsi) {
      const v = computeRsi(closes)[idx];
      if (v != null) extras.push({ label: "RSI", value: v.toFixed(2), color: T.rsi });
    }
    return extras;
  }

  private maybeLoadHistory(): void {
    if (!this.onNeedMoreHistory || this.isLoadingHistory) return;
    if (this.viewport.from < this.historyThreshold) {
      this.onNeedMoreHistory();
    }
  }

  private exitLiveOnPan(): void {
    if (!this.liveMode) return;
    const len = this.candles.length;
    // Still at the right edge → stay live
    if (this.viewport.to >= len - 1) return;
    this.liveMode = false;
  }

  private onPointerDown = (e: PointerEvent): void => {
    if (this.mode === "overview") return;
    const rect = this.canvasEl.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const L = this.layout();

    if (L.showRsi && Math.abs(y - L.rsiTop) < 4) {
      this.paneDrag = "rsi";
      this.canvasEl.setPointerCapture(e.pointerId);
      return;
    }
    if (L.showMacd && Math.abs(y - L.macdTop) < 4) {
      this.paneDrag = "macd";
      this.canvasEl.setPointerCapture(e.pointerId);
      return;
    }

    const handled = this.drawingEngine.handlePointerDown({
      x,
      y,
      button: e.button,
      pointerId: e.pointerId,
    });

    // Markets legacy callback when objects added — sync last object
    if (handled && this.onDrawingComplete) {
      const all = this.drawingEngine.manager.getAll();
      const last = all[all.length - 1];
      if (last) this.onDrawingComplete(objectToLegacy(last));
    }

    if (handled) {
      this.canvasEl.setPointerCapture(e.pointerId);
      return;
    }

    // Pan / zoom
    this.dragging = true;
    this.dragLastX = x;
    this.canvasEl.setPointerCapture(e.pointerId);
  };

  private onPointerMove = (e: PointerEvent): void => {
    const rect = this.canvasEl.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const L = this.layout();

    if (this.paneDrag) {
      const available = L.plotBottom - PAD_TOP;
      if (this.paneDrag === "rsi") {
        this.rsiFrac = Math.min(
          0.35,
          Math.max(0.1, (L.plotBottom - y) / available - (L.showMacd ? this.macdFrac : 0)),
        );
      } else {
        this.macdFrac = Math.min(0.35, Math.max(0.1, (L.plotBottom - y) / available));
      }
      this.dirty = true;
      return;
    }

    if (this.mode === "advanced") {
      const index = this.viewport.xToIndex(x, L.plotLeft, L.plotWidth);
      const price = this.yToPrice(y, L.mainTop, L.mainH);
      this.crosshair = {
        x: Math.min(L.plotWidth, Math.max(0, x)),
        y: Math.min(L.mainTop + L.mainH, Math.max(L.mainTop, y)),
        barIndex: index,
        price,
        visible: x <= L.plotWidth,
      };
      this.emitCrosshair();
      this.dirty = true;
    }

    if (this.drawingEngine.handlePointerMove({ x, y })) {
      return;
    }

    if (this.dragging) {
      const dx = x - this.dragLastX;
      this.dragLastX = x;
      if (this.tool === "zoom") {
        const factor = dx > 0 ? 0.98 : 1.02;
        this.viewport.zoomAt(
          this.viewport.xToIndex(x, L.plotLeft, L.plotWidth),
          factor,
          this.candles.length,
        );
      } else {
        const deltaBars = -(dx / Math.max(1, L.plotWidth)) * this.viewport.span;
        this.viewport.pan(deltaBars, this.candles.length);
        this.exitLiveOnPan();
        this.maybeLoadHistory();
      }
      this.onViewportChange?.(this.viewport.clone());
      this.dirty = true;
    }
  };

  private onPointerUp = (): void => {
    if (this.paneDrag) {
      this.paneDrag = null;
      return;
    }
    const before = this.drawingEngine.manager.getAll().length;
    this.drawingEngine.handlePointerUp();
    const after = this.drawingEngine.manager.getAll();
    if (this.onDrawingComplete && after.length > before) {
      this.onDrawingComplete(objectToLegacy(after[after.length - 1]));
    }
    this.dragging = false;
    this.dirty = true;
  };

  private onPointerLeave = (): void => {
    this.crosshair.visible = false;
    this.dirty = true;
  };

  private onWheel = (e: WheelEvent): void => {
    if (this.mode === "overview") return;
    e.preventDefault();
    const rect = this.canvasEl.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const L = this.layout();
    const anchor = this.viewport.xToIndex(x, L.plotLeft, L.plotWidth);
    const factor = e.deltaY > 0 ? 1.1 : 0.9;
    this.viewport.zoomAt(anchor, factor, this.candles.length);
    this.maybeLoadHistory();
    this.onViewportChange?.(this.viewport.clone());
    this.dirty = true;
  };

  private onKeyDown = (e: KeyboardEvent): void => {
    if (this.mode === "overview") return;
    const target = e.target as HTMLElement | null;
    if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;

    const mod = e.ctrlKey || e.metaKey;
    if (mod && e.key.toLowerCase() === "z") {
      e.preventDefault();
      if (e.shiftKey) this.redo();
      else this.undo();
      return;
    }
    if (mod && e.key.toLowerCase() === "y") {
      e.preventDefault();
      this.redo();
      return;
    }
    if (mod && e.key.toLowerCase() === "c") {
      e.preventDefault();
      this.drawingEngine.manager.copySelected();
      return;
    }
    if (mod && e.key.toLowerCase() === "v") {
      e.preventDefault();
      this.drawingEngine.manager.paste();
      this.dirty = true;
      return;
    }
    if (e.key === "Delete" || e.key === "Backspace") {
      const ids = this.drawingEngine.manager.getSelected().map((o) => o.id);
      if (ids.length) {
        e.preventDefault();
        this.drawingEngine.manager.remove(ids);
        this.dirty = true;
      }
      return;
    }
    if (e.key === "Escape") {
      this.drawingEngine.cancel();
      return;
    }
    if (e.key === " " || e.code === "Space") {
      e.preventDefault();
      this.tool = "hand";
      this.drawingEngine.setTool("hand");
      return;
    }
    const hotkeys: Record<string, DrawingTool> = {
      t: "trend",
      h: "hline",
      r: "rect",
      f: "fib",
      m: "measure",
      v: "vline",
    };
    const hk = hotkeys[e.key.toLowerCase()];
    if (hk && !mod) {
      this.tool = hk;
      this.drawingEngine.setTool(hk);
      return;
    }

    if (e.key === "ArrowLeft") {
      this.viewport.pan(-this.viewport.span * 0.05, this.candles.length);
      this.exitLiveOnPan();
      this.maybeLoadHistory();
      this.dirty = true;
    } else if (e.key === "ArrowRight") {
      this.viewport.pan(this.viewport.span * 0.05, this.candles.length);
      if (this.viewport.to >= this.candles.length - 1) this.liveMode = true;
      this.dirty = true;
    } else if (e.key === "+" || e.key === "=") {
      this.viewport.zoomAt((this.viewport.from + this.viewport.to) / 2, 0.9, this.candles.length);
      this.dirty = true;
    } else if (e.key === "-") {
      this.viewport.zoomAt((this.viewport.from + this.viewport.to) / 2, 1.1, this.candles.length);
      this.dirty = true;
    } else if (e.key === "f" || e.key === "F") {
      // conflict with fib hotkey — only fit when Shift+F
      if (e.shiftKey) this.fitContent();
    }
    this.onViewportChange?.(this.viewport.clone());
  };
}

export const ChartEngine = ChartController;

export function createChart(
  canvas: HTMLCanvasElement,
  options?: EngineOptions,
): ChartController {
  return new ChartController(canvas, options);
}
