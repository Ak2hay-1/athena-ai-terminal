"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import type {
  ChartType,
  DrawingTool,
  IndicatorFlags,
} from "./chart-indicators";

interface Props {
  chartType: ChartType;
  onChartType: (t: ChartType) => void;
  indicators: IndicatorFlags;
  onToggle: (key: keyof IndicatorFlags) => void;
  tool: DrawingTool;
  onTool: (t: DrawingTool) => void;
  magnet: boolean;
  onMagnet: (v: boolean) => void;
  onClearDrawings: () => void;
  onFit: () => void;
  onZoom: (preset: "1D" | "1W" | "1M" | "ALL") => void;
  onFullscreen: () => void;
  onExport?: () => void;
  isLoadingHistory?: boolean;
  hasMoreHistory?: boolean;
  historyLabel?: string;
  onBackfill?: () => void;
  isBackfilling?: boolean;
}

function Chip({
  active,
  onClick,
  children,
  title,
}: {
  active?: boolean;
  onClick: () => void;
  children: ReactNode;
  title?: string;
}) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      className={cn(
        "rounded-sm border px-1.5 py-0.5 text-[10px] uppercase tracking-wide transition-colors",
        active
          ? "border-primary/40 bg-primary/10 text-primary"
          : "border-border text-muted hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}

export function ChartToolbar({
  chartType,
  onChartType,
  indicators,
  onToggle,
  tool,
  onTool,
  magnet,
  onMagnet,
  onClearDrawings,
  onFit,
  onZoom,
  onFullscreen,
  onExport,
  isLoadingHistory = false,
  hasMoreHistory = true,
  historyLabel,
  onBackfill,
  isBackfilling = false,
}: Props) {
  return (
    <div className="flex flex-col gap-1 border-b border-border px-2 py-1.5">
      <div className="flex flex-wrap items-center gap-1">
        <span className="mr-1 text-[10px] uppercase text-muted-foreground">
          Type
        </span>
        {(
          [
            ["candles", "Candle"],
            ["hollow", "Hollow"],
            ["line", "Line"],
            ["area", "Area"],
          ] as const
        ).map(([id, label]) => (
          <Chip
            key={id}
            active={chartType === id}
            onClick={() => onChartType(id)}
          >
            {label}
          </Chip>
        ))}

        <span className="mx-1 h-3 w-px bg-border" />

        <span className="mr-1 text-[10px] uppercase text-muted-foreground">
          Overlay
        </span>
        <Chip active={indicators.ema20} onClick={() => onToggle("ema20")}>
          EMA20
        </Chip>
        <Chip active={indicators.ema50} onClick={() => onToggle("ema50")}>
          EMA50
        </Chip>
        <Chip active={indicators.sma20} onClick={() => onToggle("sma20")}>
          SMA20
        </Chip>
        <Chip active={indicators.sma50} onClick={() => onToggle("sma50")}>
          SMA50
        </Chip>
        <Chip active={indicators.sma200} onClick={() => onToggle("sma200")}>
          SMA200
        </Chip>
        <Chip active={indicators.bollinger} onClick={() => onToggle("bollinger")}>
          BB
        </Chip>
        <Chip active={indicators.vwap} onClick={() => onToggle("vwap")}>
          VWAP
        </Chip>
        <Chip active={indicators.atr} onClick={() => onToggle("atr")}>
          ATR
        </Chip>
        <Chip active={indicators.volume} onClick={() => onToggle("volume")}>
          Vol
        </Chip>
        <Chip
          active={indicators.priceLine}
          onClick={() => onToggle("priceLine")}
        >
          Price
        </Chip>

        <span className="mx-1 h-3 w-px bg-border" />

        <span className="mr-1 text-[10px] uppercase text-muted-foreground">
          Pane
        </span>
        <Chip active={indicators.rsi} onClick={() => onToggle("rsi")}>
          RSI
        </Chip>
        <Chip active={indicators.macd} onClick={() => onToggle("macd")}>
          MACD
        </Chip>
      </div>

      <div className="flex flex-wrap items-center gap-1">
        <span className="mr-1 text-[10px] uppercase text-muted-foreground">
          Draw
        </span>
        {(
          [
            ["cursor", "Cursor"],
            ["trend", "Trend"],
            ["hline", "H-Line"],
            ["ray", "Ray"],
            ["rect", "Rect"],
            ["fib", "Fib"],
          ] as const
        ).map(([id, label]) => (
          <Chip key={id} active={tool === id} onClick={() => onTool(id)}>
            {label}
          </Chip>
        ))}
        <Chip active={magnet} onClick={() => onMagnet(!magnet)} title="Snap to OHLC">
          Magnet
        </Chip>
        <Chip active={false} onClick={onClearDrawings}>
          Clear
        </Chip>

        <span className="mx-1 h-3 w-px bg-border" />

        <span className="mr-1 text-[10px] uppercase text-muted-foreground">
          View
        </span>
        <Chip active={false} onClick={onFit}>
          Fit
        </Chip>
        {(["1D", "1W", "1M", "ALL"] as const).map((p) => (
          <Chip key={p} active={false} onClick={() => onZoom(p)}>
            {p}
          </Chip>
        ))}
        <Chip active={false} onClick={onFullscreen}>
          Full
        </Chip>
        {onExport ? (
          <Chip active={false} onClick={onExport}>
            PNG
          </Chip>
        ) : null}

        {onBackfill ? (
          <>
            <span className="mx-1 h-3 w-px bg-border" />
            <Chip active={isBackfilling} onClick={onBackfill}>
              {isBackfilling ? "Backfilling…" : "Backfill"}
            </Chip>
          </>
        ) : null}

        <span className="ml-auto text-[10px] text-muted-foreground">
          {isLoadingHistory
            ? "Loading history…"
            : hasMoreHistory
              ? (historyLabel ?? "Scroll left for older bars")
              : (historyLabel ?? "End of history")}
        </span>
      </div>
    </div>
  );
}
