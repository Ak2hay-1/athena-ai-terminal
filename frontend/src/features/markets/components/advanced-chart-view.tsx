"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { MARKET_SYMBOLS, TIMEFRAMES, priceDigitsFor } from "@/constants/markets";
import {
  PriceChart,
  type ChartMarker,
} from "@/features/markets/components/price-chart";
import { useCandleHistory } from "@/hooks/use-candle-history";
import { useMarketWebSocket } from "@/hooks/use-market-websocket";
import { mapRecommendation, toNumber } from "@/lib/mappers";
import { applyQuoteToCandle, formatPrice } from "@/lib/utils";
import { SymbolSearchSelect } from "@/modules/athena-chart/components/SymbolSearchSelect";
import { ApiError } from "@/services/api-client";
import {
  backfillCandles,
  getMarketStatistics,
  getQuotes,
} from "@/services/market";
import { getLatestRecommendation } from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";
import type { Candle } from "@/types";

function mapCandle(
  raw: Record<string, unknown>,
  fallbacks: { symbol: string; timeframe: string },
): Candle | null {
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

export function AdvancedChartView({ symbol }: { symbol: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const storeTf = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);

  const normalized = symbol.toUpperCase();
  const tfParam = searchParams.get("tf");
  const tfUpper = (tfParam ?? "").toUpperCase();
  const timeframe = (
    (TIMEFRAMES as readonly string[]).includes(tfUpper) ? tfUpper : storeTf
  ).toUpperCase();

  const enabled = Boolean(user);
  const [isBackfilling, setIsBackfilling] = useState(false);
  const [backfillError, setBackfillError] = useState<string | null>(null);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);
  const [chartHeight, setChartHeight] = useState(640);
  const [tickMid, setTickMid] = useState<number | null>(null);

  useEffect(() => {
    setSymbol(normalized);
  }, [normalized, setSymbol]);

  useEffect(() => {
    setTickMid(null);
    setBackfillError(null);
  }, [normalized, timeframe]);

  useEffect(() => {
    if (timeframe !== storeTf.toUpperCase()) {
      setTimeframe(timeframe);
    }
  }, [setTimeframe, storeTf, timeframe]);

  useEffect(() => {
    const update = () => {
      setChartHeight(Math.max(480, window.innerHeight - 140));
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  const {
    candles,
    isLoading,
    isLoadingMore,
    hasMore,
    loadOlder,
    applyLiveCandle,
  } = useCandleHistory({
    symbol: normalized,
    timeframe,
    enabled,
    refreshKey: historyRefreshKey,
  });

  const statsQuery = useQuery({
    queryKey: ["market", "statistics", normalized, timeframe],
    queryFn: () => getMarketStatistics(normalized, timeframe),
    enabled,
    staleTime: 30_000,
  });

  const recommendationQuery = useQuery({
    queryKey: ["recommendation", "latest", normalized, timeframe],
    queryFn: () => getLatestRecommendation(normalized, timeframe),
    enabled,
    staleTime: 60_000,
  });

  const onWsMessage = useCallback(
    (payload: Record<string, unknown>) => {
      if (payload.type === "tick") {
        const updateSymbol = String(payload.symbol ?? "").toUpperCase();
        if (updateSymbol !== normalized) return;
        const mid = toNumber(payload.mid);
        if (mid) setTickMid(mid);
        return;
      }

      if (payload.type !== "candle_update") return;
      const updateSymbol = String(payload.symbol ?? "").toUpperCase();
      const updateTf = String(payload.timeframe ?? "").toUpperCase();
      if (updateSymbol !== normalized || updateTf !== timeframe) return;
      const candleRaw = payload.candle as Record<string, unknown> | undefined;
      const mapped = candleRaw
        ? mapCandle(candleRaw, { symbol: normalized, timeframe })
        : null;
      if (mapped) applyLiveCandle(mapped);

      if (payload.recommendation) {
        const mappedRec = mapRecommendation(
          payload.recommendation as Record<string, unknown>,
          { symbol: normalized, timeframe },
        );
        if (mappedRec) {
          queryClient.setQueryData(
            ["recommendation", "latest", normalized, timeframe],
            mappedRec,
          );
        }
      }
    },
    [applyLiveCandle, normalized, queryClient, timeframe],
  );

  const { connected } = useMarketWebSocket({
    symbols: [normalized],
    timeframe,
    onMessage: onWsMessage,
    enabled,
  });

  const quoteQuery = useQuery({
    queryKey: ["market", "quotes", normalized, timeframe],
    queryFn: () => getQuotes([normalized], timeframe),
    enabled,
    // Prefer WS ticks when connected; keep a slow REST fallback.
    refetchInterval: connected ? 10_000 : 1_000,
    staleTime: connected ? 5_000 : 500,
  });

  const quote = quoteQuery.data?.[0];
  const lastCandle = candles.at(-1) ?? null;
  const liveMid = tickMid ?? quote?.mid ?? null;
  const liveCandle = useMemo(() => {
    if (!lastCandle) return null;
    if (liveMid) return applyQuoteToCandle(lastCandle, liveMid);
    return lastCandle;
  }, [lastCandle, liveMid]);

  const recommendation = recommendationQuery.data ?? null;
  const levels =
    recommendation &&
    (recommendation.signal.includes("BUY") ||
      recommendation.signal.includes("SELL"))
      ? {
          entry: recommendation.entry,
          stopLoss: recommendation.stopLoss,
          takeProfit: recommendation.takeProfit,
        }
      : null;

  const markers: ChartMarker[] = [];
  if (
    recommendation?.createdAt &&
    (recommendation.signal.includes("BUY") ||
      recommendation.signal.includes("SELL"))
  ) {
    const buy = recommendation.signal.includes("BUY");
    markers.push({
      time: recommendation.createdAt,
      position: buy ? "belowBar" : "aboveBar",
      shape: buy ? "arrowUp" : "arrowDown",
      color: buy ? "#00d46a" : "#ff4d4d",
      text: recommendation.signal.replace("_", " "),
    });
  }

  const lastPrice = liveMid ?? liveCandle?.close ?? 0;
  const digits = priceDigitsFor(normalized, lastPrice);
  const quotesLive = Boolean(liveMid);
  const stats = statsQuery.data;
  const historyLabel = stats
    ? `${stats.candle_count.toLocaleString()} bars` +
      (stats.first_candle
        ? ` · from ${new Date(stats.first_candle).toLocaleDateString()}`
        : "")
    : undefined;

  const handleBackfill = useCallback(async () => {
    if (isBackfilling) return;
    setIsBackfilling(true);
    setBackfillError(null);
    try {
      await backfillCandles(normalized, timeframe);
      await queryClient.invalidateQueries({
        queryKey: ["market", "statistics", normalized, timeframe],
      });
      setHistoryRefreshKey((n) => n + 1);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Backfill failed. Check MT5 credentials and try again.";
      setBackfillError(message);
    } finally {
      setIsBackfilling(false);
    }
  }, [isBackfilling, normalized, queryClient, timeframe]);

  const pushTf = (next: string) => {
    setTimeframe(next);
    router.replace(
      `/markets/${normalized.toLowerCase()}/chart?tf=${encodeURIComponent(next)}`,
    );
  };

  const pushSymbol = (next: string) => {
    setSymbol(next);
    router.push(
      `/markets/${next.toLowerCase()}/chart?tf=${encodeURIComponent(timeframe)}`,
    );
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={`/markets/${normalized.toLowerCase()}`}
            className="text-xs text-muted hover:text-foreground"
          >
            ← Market
          </Link>
          <Link href="/" className="text-xs text-muted hover:text-foreground">
            Dashboard
          </Link>
          <div className="flex items-baseline gap-2">
            <h1 className="font-mono text-xl font-semibold tracking-tight">
              {normalized}
            </h1>
            <span className="font-mono text-lg tabular-nums text-primary">
              {lastPrice ? formatPrice(lastPrice, digits) : "—"}
            </span>
          </div>
          <Badge tone={connected ? "bullish" : quotesLive ? "warning" : "bearish"}>
            {connected ? "Live" : quotesLive ? "Quotes" : "Offline"}
          </Badge>
          {historyLabel ? (
            <span className="text-[11px] text-muted">{historyLabel}</span>
          ) : null}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <SymbolSearchSelect
            value={normalized}
            onChange={pushSymbol}
            symbols={MARKET_SYMBOLS}
            aria-label="Symbol"
            buttonClassName="h-9 min-w-[110px] px-3 text-sm"
          />
          <select
            value={timeframe}
            onChange={(e) => pushTf(e.target.value)}
            className="h-9 rounded-sm border border-border bg-panel px-3 font-mono text-sm outline-none focus:border-primary/50"
          >
            {TIMEFRAMES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="min-h-0 flex-1">
        {candles.length > 0 ? (
          <PriceChart
            candles={candles}
            liveCandle={liveCandle}
            levels={levels}
            markers={markers}
            height={chartHeight}
            symbol={normalized}
            timeframe={timeframe}
            onNeedMoreHistory={hasMore ? loadOlder : undefined}
            isLoadingHistory={isLoadingMore}
            hasMoreHistory={hasMore}
            historyLabel={historyLabel}
            onBackfill={enabled ? () => void handleBackfill() : undefined}
            isBackfilling={isBackfilling}
            className="h-full"
          />
        ) : (
          <div className="flex h-[60vh] flex-col items-center justify-center gap-3 rounded-sm border border-dashed border-border text-sm text-muted">
            {!enabled
              ? "Sign in to open the advanced chart"
              : isLoading
                ? `Loading ${normalized} ${timeframe}…`
                : `No candle data for ${normalized} ${timeframe}`}
            {enabled && !isLoading ? (
              <>
                <button
                  type="button"
                  disabled={isBackfilling}
                  onClick={() => void handleBackfill()}
                  className="rounded-sm border border-primary/40 bg-primary/10 px-3 py-1.5 text-xs text-primary"
                >
                  {isBackfilling ? "Backfilling…" : "Backfill from MT5"}
                </button>
                {backfillError ? (
                  <p className="max-w-md px-4 text-center text-xs text-bearish">
                    {backfillError}
                  </p>
                ) : null}
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
