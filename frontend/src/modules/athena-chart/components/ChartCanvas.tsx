"use client";

import { useEffect, useRef } from "react";
import { ChartController } from "../engine/controller";
import type { Candlestick, DrawingObject, SmartCursorInfo } from "../types";
import { useDrawingStore } from "../store/drawing-store";
import { useIndicatorStore } from "../store/indicator-store";
import { useViewportStore } from "../store/viewport-store";
import { useChartUiStore } from "../store/ui-store";
import { useSessionStore } from "../store/session-store";
import { useIntelligenceStore } from "../intelligence/store/intelligence-store";
import { useIntelligenceAnalysis } from "../intelligence/services/useIntelligenceAnalysis";
import { useDecisionStore } from "../decision-engine/store/decision-store";
import { useDecisionEngine } from "../decision-engine/services/useDecisionEngine";
import { useChartStore } from "../store/chart-store";
import { useCopilot } from "../copilot/services/useCopilot";
import type { ExplainTarget } from "../copilot/types";

interface ChartCanvasProps {
  candles: Candlestick[];
  liveCandle?: Candlestick | null;
  engineRef: React.MutableRefObject<ChartController | null>;
  onNeedMoreHistory?: () => void;
  isLoadingHistory?: boolean;
  hasMoreHistory?: boolean;
  liveMode?: boolean;
}

function liveKey(c: Candlestick | null | undefined): string {
  if (!c) return "";
  return `${c.time}:${c.open}:${c.high}:${c.low}:${c.close}:${c.tick_volume}`;
}

type CrosshairExtras = Array<{ label: string; value: string; color?: string }>;

function resolveExplainTarget(
  smart: SmartCursorInfo | null,
  candle: Candlestick | null,
  intel: ReturnType<typeof useIntelligenceStore.getState>["snapshot"],
  decision: ReturnType<typeof useDecisionStore.getState>["opportunity"],
  selectedDrawingIds: string[],
  drawings: DrawingObject[],
): ExplainTarget {
  if (selectedDrawingIds.length) {
    const d = drawings.find((x) => x.id === selectedDrawingIds[0]);
    if (d) {
      return {
        kind: "trendline",
        id: d.id,
        label: `${d.type} drawing`,
        extras: { type: d.type },
      };
    }
  }

  const price = smart?.price ?? candle?.close;
  if (intel && price != null) {
    const ob = intel.orderBlocks.find(
      (o) => o.status === "active" && price <= o.top && price >= o.bottom,
    );
    if (ob) {
      return {
        kind: "order_block",
        id: ob.id,
        label: `${ob.bias} order block`,
        price,
      };
    }
    const fvg = intel.fvgs.find(
      (f) =>
        (f.status === "active" || f.status === "partial") &&
        price <= f.top &&
        price >= f.bottom,
    );
    if (fvg) {
      return {
        kind: "fvg",
        id: fvg.id,
        label: `${fvg.bias} FVG (${fvg.status})`,
        price,
      };
    }
    const liq = intel.liquidity
      .slice()
      .sort((a, b) => Math.abs(a.price - price) - Math.abs(b.price - price))[0];
    if (liq && Math.abs(liq.price - price) / price < 0.0015) {
      return {
        kind: "liquidity",
        id: liq.id,
        label: liq.kind.replace(/_/g, " "),
        price: liq.price,
      };
    }
    const struct = intel.structure[intel.structure.length - 1];
    if (struct) {
      return {
        kind: "structure",
        id: struct.id,
        label: `${struct.label} ${struct.direction}`,
        price: struct.price,
      };
    }
  }

  if (decision && decision.direction !== "flat") {
    return {
      kind: "trade",
      id: decision.id,
      label: `${decision.bias} ${decision.grade}`,
      price: decision.activeEntry.entry,
    };
  }

  return {
    kind: "candle",
    label: candle
      ? `Candle ${candle.time} O${candle.open} H${candle.high} L${candle.low} C${candle.close}`
      : smart
        ? `Price ${smart.price}`
        : "Chart focus",
    price: price ?? undefined,
    time: candle?.time,
  };
}

export function ChartCanvas({
  candles,
  liveCandle = null,
  engineRef,
  onNeedMoreHistory,
  isLoadingHistory = false,
  hasMoreHistory = true,
  liveMode = true,
}: ChartCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const live = liveKey(liveCandle);
  const symbol = useChartStore((s) => s.symbol);
  const timeframe = useChartStore((s) => s.timeframe);
  useIntelligenceAnalysis(candles, symbol, timeframe);
  useDecisionEngine(candles, symbol, timeframe);
  const { explainTarget } = useCopilot(candles);
  const intelSnapshot = useIntelligenceStore((s) => s.snapshot);
  const intelOverlays = useIntelligenceStore((s) => s.settings.overlays);
  const decisionSnapshot = useDecisionStore((s) => s.snapshot);
  const decisionOverlays = useDecisionStore((s) => s.settings.overlays);
  const tool = useDrawingStore((s) => s.tool);
  const magnetMode = useDrawingStore((s) => s.magnetMode);
  const objects = useDrawingStore((s) => s.objects);
  const selectedIds = useDrawingStore((s) => s.selectedIds);
  const setObjects = useDrawingStore((s) => s.setObjects);
  const setSelectedIds = useDrawingStore((s) => s.setSelectedIds);
  const setHistoryFlags = useDrawingStore((s) => s.setHistoryFlags);
  const setContextMenu = useDrawingStore((s) => s.setContextMenu);
  const setTextEdit = useDrawingStore((s) => s.setTextEdit);
  const flags = useIndicatorStore((s) => s.flags);
  const instances = useIndicatorStore((s) => s.instances);
  const setViewport = useViewportStore((s) => s.setViewport);
  const setHoverPrice = useChartUiStore((s) => s.setHoverPrice);
  const setSmartCursor = useChartUiStore((s) => s.setSmartCursor);
  const smartCursor = useChartUiStore((s) => s.smartCursor);
  const setFps = useChartUiStore((s) => s.setFps);
  const showSessions = useSessionStore((s) => s.enabled);
  const sessionFlags = useSessionStore((s) => s.flags);
  const setRightTab = useChartUiStore((s) => s.setRightTab);
  const explainOnClick = true;

  const seriesKey = candles[0]
    ? `${candles[0].symbol}:${candles[0].timeframe}`
    : "empty";

  useEffect(() => {
    if (!canvasRef.current) return;
    const engine = new ChartController(canvasRef.current, {
      mode: "advanced",
      chartType: "candles",
      indicators: flags,
      drawingObjects: objects,
      tool,
      magnetMode,
      showSessions,
      sessionFlags,
      intelligenceSnapshot: intelSnapshot,
      intelligenceOverlays: intelOverlays,
      decisionSnapshot,
      decisionOverlays,
      onNeedMoreHistory: hasMoreHistory ? onNeedMoreHistory : undefined,
      isLoadingHistory,
      historyThreshold: 80,
      onDrawingsChange: (objs: DrawingObject[]) => setObjects(objs),
      onSelectionChange: setSelectedIds,
      onHistoryChange: setHistoryFlags,
      onContextMenu: (req) => setContextMenu(req),
      onTextEdit: (id, text, screen) => setTextEdit({ id, text, ...screen }),
      onCrosshair: (
        c: Candlestick | null,
        _extras: CrosshairExtras,
        smart?: SmartCursorInfo | null,
      ) => {
        setHoverPrice(c?.close ?? null);
        setSmartCursor(smart ?? null);
      },
      onFps: setFps,
      onViewportChange: setViewport,
    });
    engine.indicatorManager.setInstances(instances);
    engine.setLiveMode(liveMode);
    engineRef.current = engine;
    engine.setCandles(candles);
    return () => {
      engine.destroy();
      engineRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seriesKey]);

  useEffect(() => {
    engineRef.current?.applyOptions({
      indicators: flags,
      drawingObjects: objects,
      tool,
      magnetMode,
      showSessions,
      sessionFlags,
      intelligenceSnapshot: intelSnapshot,
      intelligenceOverlays: intelOverlays,
      decisionSnapshot,
      decisionOverlays,
      onDrawingsChange: setObjects,
      onSelectionChange: setSelectedIds,
      onHistoryChange: setHistoryFlags,
      onContextMenu: (req) => setContextMenu(req),
      onTextEdit: (id, text, screen) => setTextEdit({ id, text, ...screen }),
      onCrosshair: (c, _e, smart) => {
        setHoverPrice(c?.close ?? null);
        setSmartCursor(smart ?? null);
      },
      onFps: setFps,
      onViewportChange: setViewport,
    });
    engineRef.current?.indicatorManager.setInstances(instances);
  }, [
    flags,
    objects,
    tool,
    magnetMode,
    instances,
    showSessions,
    sessionFlags,
    intelSnapshot,
    intelOverlays,
    decisionSnapshot,
    decisionOverlays,
    setObjects,
    setSelectedIds,
    setHistoryFlags,
    setContextMenu,
    setTextEdit,
    setHoverPrice,
    setSmartCursor,
    setFps,
    setViewport,
    engineRef,
  ]);

  useEffect(() => {
    engineRef.current?.setCandles(candles);
  }, [candles, engineRef]);

  useEffect(() => {
    if (liveCandle) engineRef.current?.updateLive(liveCandle);
  }, [live, liveCandle, engineRef]);

  useEffect(() => {
    engineRef.current?.setLiveMode(liveMode);
  }, [liveMode, engineRef]);

  useEffect(() => {
    engineRef.current?.applyOptions({
      onNeedMoreHistory: hasMoreHistory ? onNeedMoreHistory : undefined,
      isLoadingHistory,
      historyThreshold: 80,
    });
  }, [hasMoreHistory, isLoadingHistory, onNeedMoreHistory, engineRef]);

  useEffect(() => {
    const el = canvasRef.current;
    if (!el || !explainOnClick) return;
    const onDblClick = () => {
      const candle =
        candles.find(
          (c) =>
            smartCursor &&
            Math.abs(
              new Date(c.time).getTime() / 1000 - smartCursor.timeSec,
            ) < 2,
        ) ?? candles[candles.length - 1] ?? null;
      const target = resolveExplainTarget(
        smartCursor,
        candle,
        useIntelligenceStore.getState().snapshot,
        useDecisionStore.getState().opportunity,
        selectedIds,
        objects,
      );
      setRightTab("ai");
      void explainTarget(target);
    };
    el.addEventListener("dblclick", onDblClick);
    return () => el.removeEventListener("dblclick", onDblClick);
  }, [
    explainOnClick,
    smartCursor,
    candles,
    selectedIds,
    objects,
    explainTarget,
    setRightTab,
  ]);

  return <canvas ref={canvasRef} className="block h-full w-full" />;
}
