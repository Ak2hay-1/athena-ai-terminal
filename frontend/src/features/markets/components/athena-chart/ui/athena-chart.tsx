"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { HISTORY_VISIBLE_THRESHOLD } from "@/lib/candle-history";
import { cn } from "@/lib/utils";
import type { Candle } from "@/types";
import {
  DEFAULT_INDICATORS,
  barsForZoomPreset,
  type ChartType,
  type IndicatorFlags,
} from "../../chart/chart-indicators";
import { ChartLegend } from "../../chart/chart-legend";
import { ChartToolbar } from "../../chart/chart-toolbar";
import { useChartDrawings } from "../../chart/use-chart-drawings";
import {
  ChartController,
  type ChartLevels,
  type ChartMarker,
  type Candlestick,
} from "@/modules/athena-chart";

export type { ChartMarker, ChartLevels };

interface Props {
  candles: Candle[];
  height?: number;
  className?: string;
  liveCandle?: Candle | null;
  levels?: ChartLevels | null;
  showToolbar?: boolean;
  onNeedMoreHistory?: () => void;
  historyThreshold?: number;
  isLoadingHistory?: boolean;
  hasMoreHistory?: boolean;
  symbol?: string;
  timeframe?: string;
  markers?: ChartMarker[];
  onBackfill?: () => void;
  isBackfilling?: boolean;
  historyLabel?: string;
  mode?: "advanced" | "overview";
}

function candlesKey(candles: Candle[]): string {
  if (candles.length === 0) return "0";
  const first = candles[0];
  const last = candles[candles.length - 1];
  return `${candles.length}:${first.time}:${last.time}:${last.close}:${last.tick_volume}`;
}

function liveKey(c: Candle | null): string {
  if (!c) return "";
  return `${c.time}:${c.open}:${c.high}:${c.low}:${c.close}:${c.tick_volume}`;
}

export function AthenaChart({
  candles,
  height = 420,
  className,
  liveCandle = null,
  levels = null,
  showToolbar = true,
  onNeedMoreHistory,
  historyThreshold = HISTORY_VISIBLE_THRESHOLD,
  isLoadingHistory = false,
  hasMoreHistory = true,
  symbol = "",
  timeframe = "M5",
  markers = [],
  onBackfill,
  isBackfilling = false,
  historyLabel,
  mode = "advanced",
}: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<ChartController | null>(null);

  const [chartType, setChartType] = useState<ChartType>("candles");
  const [indicators, setIndicators] = useState<IndicatorFlags>(DEFAULT_INDICATORS);
  const [hoverCandle, setHoverCandle] = useState<Candle | null>(null);
  const [legendExtras, setLegendExtras] = useState<
    Array<{ label: string; value: string; color?: string }>
  >([]);

  const {
    drawings,
    addDrawing,
    clearDrawings,
    tool,
    setTool,
    magnet,
    setMagnet,
  } = useChartDrawings(symbol, timeframe);

  const toolbarH = showToolbar && mode === "advanced" ? 58 : 0;
  const canvasH = Math.max(120, height - toolbarH);
  const dataKey = candlesKey(candles);
  const live = liveKey(liveCandle);

  const toggleIndicator = useCallback((key: keyof IndicatorFlags) => {
    setIndicators((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  useEffect(() => {
    if (!canvasRef.current) return;
    const engine = new ChartController(canvasRef.current, {
      mode,
      chartType,
      indicators,
      levels,
      markers,
      drawings,
      tool,
      magnet,
      onNeedMoreHistory,
      historyThreshold,
      isLoadingHistory,
      onDrawingComplete: (d) => {
        // Markets store only accepts legacy ChartDrawing shapes
        if (
          d.type === "hline" ||
          d.type === "trend" ||
          d.type === "ray" ||
          d.type === "rect" ||
          d.type === "fib"
        ) {
          addDrawing(d as Parameters<typeof addDrawing>[0]);
        }
      },
      onCrosshair: (c: Candlestick | null, extras: Array<{ label: string; value: string; color?: string }>) => {
        setHoverCandle(c);
        setLegendExtras(extras);
      },
    });
    engineRef.current = engine;
    engine.setCandles(candles);
    return () => {
      engine.destroy();
      engineRef.current = null;
    };
    // Recreate only when canvas host size mode changes meaningfully
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, canvasH]);

  useEffect(() => {
    engineRef.current?.applyOptions({
      chartType: mode === "overview" ? "area" : chartType,
      indicators:
        mode === "overview"
          ? { ...DEFAULT_INDICATORS, ema20: false, ema50: false, volume: false, priceLine: true, rsi: false, macd: false }
          : indicators,
      levels,
      markers,
      drawings,
      tool,
      magnet,
      onNeedMoreHistory,
      historyThreshold,
      isLoadingHistory,
      onDrawingComplete: (d) => {
        // Markets store only accepts legacy ChartDrawing shapes
        if (
          d.type === "hline" ||
          d.type === "trend" ||
          d.type === "ray" ||
          d.type === "rect" ||
          d.type === "fib"
        ) {
          addDrawing(d as Parameters<typeof addDrawing>[0]);
        }
      },
    });
  }, [
    mode,
    chartType,
    indicators,
    levels,
    markers,
    drawings,
    tool,
    magnet,
    onNeedMoreHistory,
    historyThreshold,
    isLoadingHistory,
    addDrawing,
  ]);

  useEffect(() => {
    engineRef.current?.setCandles(candles);
  }, [dataKey, candles]);

  useEffect(() => {
    if (liveCandle) engineRef.current?.updateLive(liveCandle);
  }, [live, liveCandle]);

  const onFit = useCallback(() => engineRef.current?.fitContent(), []);
  const onZoom = useCallback(
    (preset: "1D" | "1W" | "1M" | "ALL") => {
      const bars = barsForZoomPreset(timeframe, preset);
      engineRef.current?.zoomPreset(bars);
    },
    [timeframe],
  );
  const onFullscreen = useCallback(() => {
    const el = rootRef.current;
    if (!el) return;
    if (document.fullscreenElement) void document.exitFullscreen();
    else void el.requestFullscreen();
  }, []);

  const onExport = useCallback(() => {
    const url = engineRef.current?.exportPng();
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = `${symbol || "athena"}-${timeframe}-chart.png`;
    a.click();
  }, [symbol, timeframe]);

  return (
    <div
      ref={rootRef}
      className={cn(
        "relative w-full overflow-hidden rounded-sm border border-border bg-panel",
        className,
      )}
      style={{ height }}
      tabIndex={0}
    >
      {showToolbar && mode === "advanced" ? (
        <ChartToolbar
          chartType={chartType}
          onChartType={setChartType}
          indicators={indicators}
          onToggle={toggleIndicator}
          tool={tool}
          onTool={setTool}
          magnet={magnet}
          onMagnet={setMagnet}
          onClearDrawings={clearDrawings}
          onFit={onFit}
          onZoom={onZoom}
          onFullscreen={onFullscreen}
          onExport={onExport}
          isLoadingHistory={isLoadingHistory}
          hasMoreHistory={hasMoreHistory}
          historyLabel={historyLabel}
          onBackfill={onBackfill}
          isBackfilling={isBackfilling}
        />
      ) : null}

      <div className="relative" style={{ height: canvasH }}>
        {mode === "advanced" ? (
          <ChartLegend candle={hoverCandle} extras={legendExtras} />
        ) : null}
        <canvas ref={canvasRef} className="block h-full w-full" />
      </div>
    </div>
  );
}

/** Drop-in alias matching previous PriceChart export name. */
export const PriceChart = AthenaChart;
