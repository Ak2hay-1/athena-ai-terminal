"use client";

import { useRef } from "react";
import type { ChartController } from "../engine/controller";
import type { Candlestick } from "../types";
import { useChartStore } from "../store/chart-store";
import { ChartCanvas } from "./ChartCanvas";
import { LoadingOverlay } from "./LoadingOverlay";

interface ChartContainerProps {
  candles: Candlestick[];
  liveCandle?: Candlestick | null;
  engineRef: React.MutableRefObject<ChartController | null>;
  onNeedMoreHistory?: () => void;
  isLoadingHistory?: boolean;
  hasMoreHistory?: boolean;
  liveMode?: boolean;
}

export function ChartContainer({
  candles,
  liveCandle = null,
  engineRef,
  onNeedMoreHistory,
  isLoadingHistory = false,
  hasMoreHistory = true,
  liveMode = true,
}: ChartContainerProps) {
  const loading = useChartStore((s) => s.loading);
  const error = useChartStore((s) => s.error);
  const hostRef = useRef<HTMLDivElement>(null);

  return (
    <div ref={hostRef} className="relative min-h-0 min-w-0 flex-1 bg-[#0d0d0d]">
      <LoadingOverlay visible={loading && candles.length === 0} />
      {!loading && candles.length === 0 && error ? (
        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
          <p className="rounded-sm border border-border bg-black/70 px-3 py-2 font-mono text-[11px] text-muted">
            {error}
          </p>
        </div>
      ) : null}
      <ChartCanvas
        candles={candles}
        liveCandle={liveCandle}
        engineRef={engineRef}
        onNeedMoreHistory={onNeedMoreHistory}
        isLoadingHistory={isLoadingHistory}
        hasMoreHistory={hasMoreHistory}
        liveMode={liveMode}
      />
    </div>
  );
}
