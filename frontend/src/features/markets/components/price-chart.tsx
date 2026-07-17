"use client";

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import type { Candle } from "@/types";
import { cn } from "@/lib/utils";

interface Props {
  candles: Candle[];
  height?: number;
  className?: string;
  liveCandle?: Candle | null;
}

function toChartPoint(candle: Candle) {
  return {
    time: Math.floor(new Date(candle.time).getTime() / 1000) as UTCTimestamp,
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
  };
}

/** Stable primitive key — keeps useEffect deps fixed-length (never the candles array itself). */
function candlesKey(candles: Candle[]): string {
  if (candles.length === 0) return "0";
  const first = candles[0];
  const last = candles[candles.length - 1];
  return `${candles.length}:${first.time}:${last.time}:${last.open}:${last.high}:${last.low}:${last.close}`;
}

function liveCandleKey(liveCandle: Candle | null): string {
  if (!liveCandle) return "";
  return `${liveCandle.time}:${liveCandle.open}:${liveCandle.high}:${liveCandle.low}:${liveCandle.close}`;
}

export function PriceChart({
  candles,
  height = 360,
  className,
  liveCandle = null,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const fittedRef = useRef(false);
  const candlesRef = useRef(candles);
  const liveCandleRef = useRef(liveCandle);
  candlesRef.current = candles;
  liveCandleRef.current = liveCandle;

  const dataKey = candlesKey(candles);
  const liveKey = liveCandleKey(liveCandle);

  // #region agent log
  {
    const heightDeps = [height];
    const candlesDeps = [dataKey];
    const liveDeps = [liveKey];
    fetch("http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "7cded5",
      },
      body: JSON.stringify({
        sessionId: "7cded5",
        runId: "post-fix",
        hypothesisId: "B,E",
        location: "price-chart.tsx:render",
        message: "PriceChart render deps snapshot",
        data: {
          candlesIsArray: Array.isArray(candles),
          candlesLength: Array.isArray(candles) ? candles.length : null,
          heightDepsLen: heightDeps.length,
          candlesDepsLen: candlesDeps.length,
          liveDepsLen: liveDeps.length,
          candlesDepsArePrimitives: typeof candlesDeps[0] === "string",
          liveDepsArePrimitives: typeof liveDeps[0] === "string",
          dataKeyLen: dataKey.length,
          liveKeyLen: liveKey.length,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
  }
  // #endregion

  useEffect(() => {
    // #region agent log
    fetch("http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "7cded5",
      },
      body: JSON.stringify({
        sessionId: "7cded5",
        runId: "post-fix",
        hypothesisId: "B,E",
        location: "price-chart.tsx:effect-height",
        message: "height effect ran",
        data: { depsLen: 1, height },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#0d0d0d" },
        textColor: "#9a9a9a",
        fontFamily: "var(--font-ibm-plex-mono), ui-monospace, monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#1c1c1c" },
        horzLines: { color: "#1c1c1c" },
      },
      rightPriceScale: {
        borderColor: "#2a2a2a",
      },
      timeScale: {
        borderColor: "#2a2a2a",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        vertLine: { color: "#ff6b00", labelBackgroundColor: "#ff6b00" },
        horzLine: { color: "#ff6b00", labelBackgroundColor: "#ff6b00" },
      },
      width: containerRef.current.clientWidth,
      height,
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#00d46a",
      downColor: "#ff4d4d",
      borderVisible: false,
      wickUpColor: "#00d46a",
      wickDownColor: "#ff4d4d",
    });

    chartRef.current = chart;
    seriesRef.current = series;
    fittedRef.current = false;

    const resize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", resize);

    return () => {
      window.removeEventListener("resize", resize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      fittedRef.current = false;
    };
  }, [height]);

  useEffect(() => {
    const data = candlesRef.current;
    // #region agent log
    fetch("http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "7cded5",
      },
      body: JSON.stringify({
        sessionId: "7cded5",
        runId: "post-fix",
        hypothesisId: "B,E",
        location: "price-chart.tsx:effect-candles",
        message: "candles effect ran",
        data: {
          depsLen: 1,
          depsType: "string",
          candlesLength: data.length,
          dataKey,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    if (!seriesRef.current || data.length === 0) return;
    seriesRef.current.setData(data.map(toChartPoint));
    if (!fittedRef.current) {
      chartRef.current?.timeScale().fitContent();
      fittedRef.current = true;
    }
  }, [dataKey]);

  useEffect(() => {
    const live = liveCandleRef.current;
    // #region agent log
    fetch("http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "7cded5",
      },
      body: JSON.stringify({
        sessionId: "7cded5",
        runId: "post-fix",
        hypothesisId: "B,E",
        location: "price-chart.tsx:effect-live",
        message: "liveCandle effect ran",
        data: {
          depsLen: 1,
          depsType: "string",
          hasLive: live != null,
          liveKey,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    if (!seriesRef.current || !live) return;
    seriesRef.current.update(toChartPoint(live));
  }, [liveKey]);

  return (
    <div
      ref={containerRef}
      className={cn(
        "w-full overflow-hidden rounded-sm border border-border bg-panel",
        className,
      )}
    />
  );
}
