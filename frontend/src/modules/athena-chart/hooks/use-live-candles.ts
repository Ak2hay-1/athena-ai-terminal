"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useCandleHistory } from "@/hooks/use-candle-history";
import { useMarketWebSocket } from "@/hooks/use-market-websocket";
import { trimSeriesToCap } from "@/lib/candle-history";
import { toNumber } from "@/lib/mappers";
import { getCandles, getQuotes } from "@/services/market";
import { useAuthStore } from "@/store/auth-store";
import type { Candle } from "@/types";
import {
  TimeBucketEngine,
  type SyncStatus,
} from "../engine/time";
import type { Candlestick } from "../types";
import { useChartStore } from "../store/chart-store";
import { toApiTimeframe } from "../utils/timeframes";

function mapCandle(
  raw: Record<string, unknown>,
  fallbacks: { symbol: string; timeframe: string },
): Candlestick | null {
  const close = toNumber(raw.close);
  if (!close) return null;
  return {
    symbol: String(raw.symbol ?? fallbacks.symbol).toUpperCase(),
    timeframe: String(raw.timeframe ?? fallbacks.timeframe).toUpperCase(),
    time: String(raw.time ?? new Date().toISOString()),
    open: toNumber(raw.open, close),
    high: toNumber(raw.high, close),
    low: toNumber(raw.low, close),
    close,
    tick_volume: Math.round(toNumber(raw.tick_volume ?? raw.tickVolume)),
  };
}

function asCandlestick(c: Candle): Candlestick {
  return {
    symbol: c.symbol,
    timeframe: c.timeframe,
    time: c.time,
    open: c.open,
    high: c.high,
    low: c.low,
    close: c.close,
    tick_volume: c.tick_volume,
  };
}

export interface LiveCandlesResult {
  candles: Candlestick[];
  liveCandle: Candlestick | null;
  connected: boolean;
  isLoading: boolean;
  apiTimeframe: string | null;
  syncStatus: SyncStatus;
  dataGapFrom: string | null;
  loadOlder: () => void;
  hasMore: boolean;
  isLoadingMore: boolean;
  liveMode: boolean;
  setLiveMode: (v: boolean) => void;
}

/**
 * Live OHLCV for the Athena Chart terminal.
 * History sync + TimeBucketEngine before any tick application.
 */
export function useLiveCandles(
  symbol: string,
  timeframe: string,
): LiveCandlesResult {
  const user = useAuthStore((s) => s.user);
  const setLoading = useChartStore((s) => s.setLoading);
  const setError = useChartStore((s) => s.setError);
  const setCandleCount = useChartStore((s) => s.setCandleCount);

  const normalized = symbol.toUpperCase();
  const apiTimeframe = toApiTimeframe(timeframe);
  const enabled = Boolean(user) && Boolean(apiTimeframe);

  const engineRef = useRef<TimeBucketEngine | null>(null);
  const ticksPausedRef = useRef(true);
  const syncKeyRef = useRef("");
  const historyFirstRef = useRef<string | null>(null);
  const [series, setSeries] = useState<Candlestick[]>([]);
  const [forming, setForming] = useState<Candlestick | null>(null);
  const [syncStatus, setSyncStatus] = useState<SyncStatus>("idle");
  const [dataGapFrom, setDataGapFrom] = useState<string | null>(null);
  const [liveMode, setLiveMode] = useState(true);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

  const {
    candles: history,
    isLoading,
    isLoadingMore,
    hasMore,
    loadOlder,
    applyLiveCandle,
    setCandles: setHistoryCandles,
  } = useCandleHistory({
    symbol: normalized,
    timeframe: apiTimeframe ?? "M5",
    enabled,
    refreshKey: historyRefreshKey,
  });

  // Sync engine from REST history on symbol/TF change, initial load, or left-pan prepend.
  // Ignore end-of-series updates from applyLiveCandle (ticks / forming bar).
  useEffect(() => {
    if (!apiTimeframe) {
      engineRef.current = null;
      syncKeyRef.current = "";
      historyFirstRef.current = null;
      setSeries([]);
      setForming(null);
      setSyncStatus("idle");
      ticksPausedRef.current = true;
      return;
    }

    if (isLoading) {
      setSyncStatus("loading");
      ticksPausedRef.current = true;
      return;
    }

    // Do not commit an empty engine — that blocks later history apply via early-return.
    if (history.length === 0) {
      engineRef.current = null;
      syncKeyRef.current = "";
      historyFirstRef.current = null;
      setSeries([]);
      setForming(null);
      setSyncStatus("idle");
      ticksPausedRef.current = true;
      return;
    }

    const key = `${normalized}:${apiTimeframe}:${historyRefreshKey}`;
    const first = history[0]?.time ?? null;
    const keyChanged = syncKeyRef.current !== key;
    const prepended =
      !keyChanged &&
      first != null &&
      historyFirstRef.current != null &&
      first !== historyFirstRef.current;
    // Recover when a prior empty/idle pass left no first-bar marker.
    const recoveredFromEmpty =
      historyFirstRef.current == null || engineRef.current == null;

    if (!keyChanged && !prepended && !recoveredFromEmpty && engineRef.current) {
      return;
    }

    syncKeyRef.current = key;
    historyFirstRef.current = first;

    try {
      const engine = new TimeBucketEngine(apiTimeframe);
      const reset = engine.reset(history.map(asCandlestick));
      engineRef.current = engine;
      const capped = trimSeriesToCap(reset);
      setSeries(capped);
      setForming(capped.at(-1) ?? null);
      setDataGapFrom(engine.getDataGapFrom());
      setSyncStatus(engine.getDataGapFrom() ? "degraded" : "ready");
      ticksPausedRef.current = false;
    } catch (err) {
      console.error("[useLiveCandles] sync failed", err);
      engineRef.current = null;
      // Fall back to raw history so the chart still paints
      const fallback = trimSeriesToCap(history.map(asCandlestick));
      setSeries(fallback);
      setForming(fallback.at(-1) ?? null);
      setSyncStatus(fallback.length > 0 ? "degraded" : "idle");
      setError(
        err instanceof Error ? err.message : "Failed to sync candle history",
      );
      ticksPausedRef.current = false;
    }
  }, [
    apiTimeframe,
    history,
    historyRefreshKey,
    isLoading,
    normalized,
    setError,
  ]);

  const resyncFromServer = useCallback(async () => {
    if (!apiTimeframe || !enabled) return;
    ticksPausedRef.current = true;
    setSyncStatus("loading");
    try {
      const batch = await getCandles(normalized, apiTimeframe, 500);
      const engine = new TimeBucketEngine(apiTimeframe);
      engineRef.current = engine;
      const merged = trimSeriesToCap(engine.reset(batch.map(asCandlestick)));
      setSeries(merged);
      setForming(merged.at(-1) ?? null);
      setDataGapFrom(engine.getDataGapFrom());
      historyFirstRef.current = batch[0]?.time ?? null;
      syncKeyRef.current = `${normalized}:${apiTimeframe}:${historyRefreshKey}`;
      setHistoryCandles(batch);
      setSyncStatus(engine.getDataGapFrom() ? "degraded" : "ready");
    } catch {
      setSyncStatus("degraded");
    } finally {
      ticksPausedRef.current = false;
    }
  }, [
    apiTimeframe,
    enabled,
    historyRefreshKey,
    normalized,
    setHistoryCandles,
  ]);

  const onReconnect = useCallback(() => {
    void resyncFromServer();
  }, [resyncFromServer]);

  const onWsMessage = useCallback(
    (payload: Record<string, unknown>) => {
      if (!apiTimeframe || ticksPausedRef.current) return;
      const engine = engineRef.current;
      if (!engine) return;

      if (payload.type === "tick") {
        const updateSymbol = String(payload.symbol ?? "").toUpperCase();
        if (updateSymbol !== normalized) return;
        // Prefer bid: the backend candle engine builds OHLC from bid
        // prices (matching broker bars), so the forming candle stays
        // consistent with persisted history.
        const mid = toNumber(payload.bid) || toNumber(payload.mid);
        if (!mid) return;
        const timeRaw = payload.time;
        const timeUtcMs =
          typeof timeRaw === "string" || typeof timeRaw === "number"
            ? new Date(timeRaw).getTime()
            : Date.now();
        if (!Number.isFinite(timeUtcMs)) return;

        const result = engine.applyTick({
          timeUtcMs,
          mid,
          symbol: normalized,
        });
        const capped = trimSeriesToCap(result.series);
        setSeries(capped);
        setForming(result.forming);
        if (result.truncated) setDataGapFrom(engine.getDataGapFrom());
        return;
      }

      if (payload.type !== "candle_update") return;
      const updateSymbol = String(payload.symbol ?? "").toUpperCase();
      const updateTf = String(payload.timeframe ?? "").toUpperCase();
      if (updateSymbol !== normalized || updateTf !== apiTimeframe) return;
      const candleRaw = payload.candle as Record<string, unknown> | undefined;
      const mapped = candleRaw
        ? mapCandle(candleRaw, { symbol: normalized, timeframe: apiTimeframe })
        : null;
      if (!mapped) return;
      const next = trimSeriesToCap(engine.applyServerCandle(mapped));
      setSeries(next);
      setForming(next.at(-1) ?? null);
      applyLiveCandle(mapped);
    },
    [apiTimeframe, applyLiveCandle, normalized],
  );

  const { connected } = useMarketWebSocket({
    symbols: [normalized],
    timeframe: apiTimeframe ?? "M5",
    onMessage: onWsMessage,
    onReconnect,
    enabled,
  });

  const quoteQuery = useQuery({
    queryKey: ["market", "quotes", "chart-terminal", normalized, apiTimeframe],
    queryFn: () => getQuotes([normalized], apiTimeframe ?? "M5"),
    enabled: enabled && syncStatus === "ready",
    refetchInterval: connected ? 10_000 : 1_000,
    staleTime: connected ? 5_000 : 500,
  });

  // REST quote mid only updates current bucket via engine (never blind stretch)
  useEffect(() => {
    if (ticksPausedRef.current || syncStatus !== "ready") return;
    const mid = quoteQuery.data?.[0]?.mid;
    const engine = engineRef.current;
    if (!mid || !engine) return;
    const result = engine.applyTick({
      timeUtcMs: Date.now(),
      mid,
      symbol: normalized,
    });
    setSeries(trimSeriesToCap(result.series));
    setForming(result.forming);
  }, [quoteQuery.data, syncStatus, normalized]);

  const liveCandle = useMemo(() => {
    if (syncStatus === "loading" || syncStatus === "idle") return null;
    return forming;
  }, [forming, syncStatus]);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      setError("Sign in to load live market data");
      setCandleCount(0);
      return;
    }
    if (!apiTimeframe) {
      setLoading(false);
      setError(`Timeframe ${timeframe} is not available for live data`);
      setCandleCount(0);
      return;
    }
    setLoading(isLoading || syncStatus === "loading");
    const gapNote = dataGapFrom
      ? ` · data gap from ${new Date(dataGapFrom).toISOString()}`
      : "";
    setError(
      !isLoading && series.length === 0
        ? "No candle history for this symbol/timeframe"
        : syncStatus === "degraded"
          ? `History incomplete${gapNote}`
          : null,
    );
    setCandleCount(series.length);
  }, [
    user,
    apiTimeframe,
    timeframe,
    isLoading,
    series.length,
    syncStatus,
    dataGapFrom,
    setLoading,
    setError,
    setCandleCount,
  ]);

  return {
    candles: series,
    liveCandle,
    connected,
    isLoading: isLoading || syncStatus === "loading",
    apiTimeframe,
    syncStatus,
    dataGapFrom,
    loadOlder,
    hasMore,
    isLoadingMore,
    liveMode,
    setLiveMode,
  };
}

/** @deprecated Use useLiveCandles — kept for module export compatibility. */
export function useMockCandles(symbol: string, timeframe: string): Candlestick[] {
  return useLiveCandles(symbol, timeframe).candles;
}
