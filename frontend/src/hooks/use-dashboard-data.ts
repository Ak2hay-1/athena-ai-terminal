"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MARKET_SYMBOLS } from "@/constants/markets";
import {
  currentSession,
  mapRecommendation,
  normalizeSignal,
  normalizeTrend,
  relativeTime,
  toNumber,
} from "@/lib/mappers";
import { getMarketHours } from "@/lib/market-hours";
import { applyQuoteToCandle } from "@/lib/utils";
import { syncNewsFeeds } from "@/services/admin";
import { getHealth } from "@/services/health";
import { getCandles, getLatestCandle, getQuotes } from "@/services/market";
import { getCalendar, getLatestNews, getNewsContext } from "@/services/news";
import {
  analyzeMarket,
  getRecommendationHistory,
  getSymbolScenario,
} from "@/services/recommendations";
import { getScannerOpportunities } from "@/services/scanner";
import { listWatchlist } from "@/services/watchlist";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";
import type {
  ActivityEvent,
  Candle,
  MarketStatus,
  Recommendation,
  ScannerOpportunity,
  TimeframeSignalSnapshot,
  WatchlistItem,
} from "@/types";
import { useMarketWebSocket } from "./use-market-websocket";

/** Chart candles may use any TF; trade signals use best-across-TFs (no TF gate). */
const WATCHLIST_PRICE_TF = "M5";
const SCANNER_PRIMARY_TF = "M15";

async function resolveWatchlistSymbols(): Promise<string[]> {
  try {
    const entries = await listWatchlist();
    const symbols = [
      ...new Set(
        entries
          .filter((entry) => entry.enabled)
          .map((entry) => entry.symbol.toUpperCase()),
      ),
    ];
    if (symbols.length > 0) return symbols;
  } catch {
    // Fall back to configured market list when watchlist API is empty/unavailable.
  }
  return [...MARKET_SYMBOLS];
}

async function buildWatchlist(): Promise<WatchlistItem[]> {
  const symbols = await resolveWatchlistSymbols();
  // Institutional desk signals come from the scanner board (qualified),
  // not best-across-TF actionable recommendations.
  const [scannerBoard, candlesBySymbol, quotes] = await Promise.all([
    getScannerOpportunities({
      timeframe: WATCHLIST_PRICE_TF,
      symbols,
      minScore: 0,
    }).catch(() => null),
    Promise.all(
      symbols.map(async (symbol) => {
        const candles = await getCandles(symbol, WATCHLIST_PRICE_TF, 3).catch(
          () => [] as Candle[],
        );
        return [symbol, candles] as const;
      }),
    ),
    getQuotes(symbols, WATCHLIST_PRICE_TF),
  ]);

  const oppMap = new Map(
    (scannerBoard?.opportunities ?? []).map((o) => [o.symbol.toUpperCase(), o]),
  );
  const candleMap = new Map(candlesBySymbol);
  const quoteMap = new Map(quotes.map((q) => [q.symbol.toUpperCase(), q.mid]));

  const rows = symbols.map((symbol) => {
    const upper = symbol.toUpperCase();
    const opp = oppMap.get(upper);
    const candles = candleMap.get(symbol) ?? [];
    const latest = candles.at(-1);
    const previous = candles.at(-2);
    const referencePrice = previous?.close ?? latest?.close ?? opp?.entry ?? 0;
    const live = quoteMap.get(upper);
    const price = live && live > 0 ? live : latest?.close ?? opp?.price ?? 0;
    const changePercent =
      price && referencePrice
        ? ((price - referencePrice) / referencePrice) * 100
        : opp?.changePercent ?? 0;

    // Prefer scanner desk signal; if missing, stand aside (do not invent BUY/SELL).
    const signal = opp?.signal ?? "NO_TRADE";
    const confidence = opp?.confidence ?? 0;
    const trend = opp?.trend
      ? normalizeTrend(opp.trend)
      : ("Neutral" as WatchlistItem["trend"]);

    return {
      symbol: upper,
      price,
      referencePrice,
      changePercent,
      signal,
      confidence,
      trend,
      setupQuality: opp?.setupQuality,
      scannerGroup: opp?.scannerGroup,
    } satisfies WatchlistItem;
  });

  // #region agent log
  {
    const _counts: Record<string, number> = {};
    for (const r of rows) _counts[r.signal] = (_counts[r.signal] ?? 0) + 1;
    fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'e72fc0'},body:JSON.stringify({sessionId:'e72fc0',runId:'post-fix',hypothesisId:'C',location:'use-dashboard-data.ts:buildWatchlist',message:'Watchlist signals from scanner board',data:{sigCounts:_counts,grpCounts:rows.reduce((a,r)=>{const g=r.scannerGroup??'unset';a[g]=(a[g]??0)+1;return a;},{} as Record<string,number>),sample:rows.slice(0,8).map((r)=>({s:r.symbol,sig:r.signal,g:r.scannerGroup,q:r.setupQuality,price:r.price}))},timestamp:Date.now()})}).catch(()=>{});
  }
  // #endregion

  return rows;
}

function mapCandle(raw: Record<string, unknown>, fallbacks: { symbol: string; timeframe: string }): Candle | null {
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

export function useDashboardData() {
  const user = useAuthStore((s) => s.user);
  const symbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const queryClient = useQueryClient();
  const enabled = Boolean(user);

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
  });

  const scenarioQuery = useQuery({
    queryKey: ["recommendation", "scenario", symbol],
    queryFn: () => getSymbolScenario(symbol),
    enabled,
    refetchInterval: 60_000,
  });

  const historyQuery = useQuery({
    queryKey: ["recommendation", "history", symbol],
    queryFn: () => getRecommendationHistory(symbol, null, 8),
    enabled,
  });

  const newsContextQuery = useQuery({
    queryKey: ["news", "context", symbol],
    queryFn: () => getNewsContext(symbol),
    enabled,
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  const newsQuery = useQuery({
    queryKey: ["news", "latest", symbol],
    queryFn: () => getLatestNews(symbol, 12),
    enabled,
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  const calendarQuery = useQuery({
    queryKey: ["news", "calendar"],
    queryFn: () => getCalendar(16),
    enabled,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const candleQuery = useQuery({
    queryKey: ["market", "latest", symbol, timeframe],
    queryFn: () => getLatestCandle(symbol, timeframe),
    enabled,
    refetchInterval: 15_000,
  });

  const watchlistQuery = useQuery({
    queryKey: ["watchlist", "live"],
    queryFn: () => buildWatchlist(),
    enabled,
    refetchInterval: 45_000,
  });

  const scannerQuery = useQuery({
    queryKey: ["scanner", "opportunities", SCANNER_PRIMARY_TF],
    queryFn: () =>
      getScannerOpportunities({
        timeframe: SCANNER_PRIMARY_TF,
        limit: 12,
        // Show full institutional desk (includes HOLD / NO_TRADE), not only BUY/SELL.
        actionableOnly: false,
      }),
    enabled,
    refetchInterval: 30_000,
  });

  const analyzeMutation = useMutation({
    // Chart TF still used to generate analysis; hero displays best-across-TFs.
    mutationFn: () => analyzeMarket(symbol, timeframe),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["recommendation", "scenario", symbol],
      });
      void queryClient.invalidateQueries({
        queryKey: ["recommendation", "history", symbol],
      });
      void queryClient.invalidateQueries({ queryKey: ["watchlist", "live"] });
      void queryClient.invalidateQueries({
        queryKey: ["scanner", "opportunities"],
      });
    },
  });

  const patchWatchlistPrice = useCallback(
    (targetSymbol: string, price: number, extras?: Partial<WatchlistItem>) => {
      if (!price) return;
      const upper = targetSymbol.toUpperCase();
      queryClient.setQueryData<WatchlistItem[]>(
        ["watchlist", "live"],
        (current) => {
          if (!current) return current;
          return current.map((item) => {
            if (item.symbol.toUpperCase() !== upper) return item;
            const reference = item.referencePrice || item.price || price;
            return {
              ...item,
              ...extras,
              price,
              changePercent:
                reference > 0
                  ? ((price - reference) / reference) * 100
                  : item.changePercent,
            };
          });
        },
      );
    },
    [queryClient],
  );

  const onWsMessage = useCallback(
    (payload: Record<string, unknown>) => {
      if (payload.type === "tick") {
        const updateSymbol = String(payload.symbol ?? "").toUpperCase();
        const mid = toNumber(payload.mid);
        if (!updateSymbol || !mid) return;
        patchWatchlistPrice(updateSymbol, mid);
        queryClient.setQueryData(
          ["scanner", "opportunities", SCANNER_PRIMARY_TF],
          (
            current:
              | { opportunities: ScannerOpportunity[]; meta: unknown }
              | undefined,
          ) => {
            if (!current?.opportunities) return current;
            return {
              ...current,
              opportunities: current.opportunities.map((item) => {
                if (item.symbol.toUpperCase() !== updateSymbol) return item;
                const reference =
                  item.price && item.changePercent != null
                    ? item.price / (1 + item.changePercent / 100)
                    : item.price ?? mid;
                return {
                  ...item,
                  price: mid,
                  changePercent:
                    reference > 0
                      ? ((mid - reference) / reference) * 100
                      : item.changePercent,
                };
              }),
            };
          },
        );
        // Keep quotes cache live for every subscribed symbol (chart mid + REST fallback).
        queryClient.setQueryData(
          ["market", "quotes", "watchlist"],
          (current: Awaited<ReturnType<typeof getQuotes>> | undefined) => {
            if (!current) {
              return [
                {
                  symbol: updateSymbol,
                  bid: toNumber(payload.bid, mid),
                  ask: toNumber(payload.ask, mid),
                  mid,
                  time: payload.time ? String(payload.time) : null,
                  source: "tick" as const,
                },
              ];
            }
            const next = current.map((q) =>
              q.symbol.toUpperCase() === updateSymbol
                ? {
                    ...q,
                    bid: toNumber(payload.bid, q.bid),
                    ask: toNumber(payload.ask, q.ask),
                    mid,
                    time: payload.time ? String(payload.time) : q.time,
                    source: "tick" as const,
                  }
                : q,
            );
            if (!next.some((q) => q.symbol.toUpperCase() === updateSymbol)) {
              next.push({
                symbol: updateSymbol,
                bid: toNumber(payload.bid, mid),
                ask: toNumber(payload.ask, mid),
                mid,
                time: payload.time ? String(payload.time) : null,
                source: "tick",
              });
            }
            return next;
          },
        );
        return;
      }

      if (payload.type !== "candle_update") return;

      const updateSymbol = String(payload.symbol ?? "").toUpperCase();
      const updateTf = String(payload.timeframe ?? "").toUpperCase();
      if (!updateSymbol || !updateTf) return;

      const candleRaw = payload.candle as Record<string, unknown> | undefined;
      const mappedCandle = candleRaw
        ? mapCandle(candleRaw, { symbol: updateSymbol, timeframe: updateTf })
        : null;

      // Chart candles only for the selected chart timeframe.
      if (updateTf === timeframe.toUpperCase() && mappedCandle) {
        if (updateSymbol === symbol.toUpperCase()) {
          queryClient.setQueryData(
            ["market", "latest", symbol, timeframe],
            mappedCandle,
          );
        }
      }

      // Price ticks from any TF candle still refresh watchlist mid.
      if (mappedCandle) {
        patchWatchlistPrice(updateSymbol, mappedCandle.close);
      }

      // Do NOT patch watchlist signal from raw candle recommendation —
      // that bypasses institutional scanner demotion (HOLD/NO_TRADE).
      // Refresh desk signals from the scanner board instead.
      if (payload.recommendation) {
        // #region agent log
        fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'e72fc0'},body:JSON.stringify({sessionId:'e72fc0',runId:'post-fix',hypothesisId:'C',location:'use-dashboard-data.ts:candle_update',message:'Skip raw rec signal patch; invalidate watchlist',data:{symbol:updateSymbol,tf:updateTf,rawSignal:(payload.recommendation as Record<string,unknown>).signal},timestamp:Date.now()})}).catch(()=>{});
        // #endregion
        void queryClient.invalidateQueries({ queryKey: ["watchlist", "live"] });
        void queryClient.invalidateQueries({
          queryKey: ["scanner", "opportunities"],
        });
        if (updateSymbol === symbol.toUpperCase()) {
          void queryClient.invalidateQueries({
            queryKey: ["recommendation", "scenario", symbol],
          });
          void queryClient.invalidateQueries({
            queryKey: ["recommendation", "history", symbol],
          });
        }
      }
    },
    [patchWatchlistPrice, queryClient, symbol, timeframe],
  );

  const wsSymbols = useMemo(() => {
    const fromWatchlist = (watchlistQuery.data ?? []).map((item) => item.symbol);
    const fromScanner = (scannerQuery.data?.opportunities ?? []).map(
      (item) => item.symbol,
    );
    const merged = [
      ...new Set(
        [...fromWatchlist, ...fromScanner]
          .map((s) => s.toUpperCase())
          .filter(Boolean),
      ),
    ];
    return merged.length > 0 ? merged : [...MARKET_SYMBOLS];
  }, [scannerQuery.data?.opportunities, watchlistQuery.data]);

  const { connected: wsConnected } = useMarketWebSocket({
    symbols: wsSymbols,
    timeframe,
    onMessage: onWsMessage,
    enabled,
  });

  const quotesQuery = useQuery({
    queryKey: ["market", "quotes", "watchlist"],
    queryFn: async () => {
      const symbols = await resolveWatchlistSymbols();
      return getQuotes(symbols, WATCHLIST_PRICE_TF);
    },
    enabled,
    // Prefer WS ticks when connected; keep a short REST poll as fallback.
    refetchInterval: wsConnected ? 3_000 : 1_000,
    staleTime: wsConnected ? 1_000 : 500,
  });

  // When WS is live, watchlist prices come from tick patches.
  // When disconnected, merge REST quotes so pairs still move.
  const watchlist = useMemo(() => {
    const base = watchlistQuery.data ?? [];
    if (wsConnected || base.length === 0) return base;

    const quotes = quotesQuery.data ?? [];
    if (quotes.length === 0) return base;

    const quoteMap = new Map(
      quotes.map((q) => [q.symbol.toUpperCase(), q.mid] as const),
    );

    return base.map((item) => {
      const mid = quoteMap.get(item.symbol.toUpperCase());
      if (mid == null || mid === 0) return item;
      const reference = item.referencePrice || item.price || mid;
      return {
        ...item,
        price: mid,
        changePercent:
          reference > 0 ? ((mid - reference) / reference) * 100 : item.changePercent,
      };
    });
  }, [quotesQuery.data, watchlistQuery.data, wsConnected]);

  const scenario = scenarioQuery.data ?? null;
  const recommendation = scenario?.best ?? null;
  const timeframeSignals: TimeframeSignalSnapshot[] = scenario?.byTimeframe ?? [];
  const quoteMid =
    quotesQuery.data?.find((q) => q.symbol.toUpperCase() === symbol.toUpperCase())
      ?.mid ?? 0;

  const symbolUpper = symbol.toUpperCase();
  const timeframeUpper = timeframe.toUpperCase();

  const queryCandle =
    candleQuery.data &&
    candleQuery.data.symbol?.toUpperCase() === symbolUpper &&
    candleQuery.data.timeframe?.toUpperCase() === timeframeUpper
      ? candleQuery.data
      : null;

  const liveCandle =
    queryCandle && quoteMid
      ? applyQuoteToCandle(queryCandle, quoteMid)
      : queryCandle;

  const marketStatus: MarketStatus = useMemo(() => {
    const score = recommendation?.confluence ?? recommendation?.confidence ?? 0;
    const volatility: MarketStatus["volatility"] =
      score >= 80 ? "High" : score >= 55 ? "Medium" : "Low";
    const hours = getMarketHours(symbol);

    return {
      session: currentSession(),
      volatility,
      marketOpen: hours.open,
      marketReason: hours.reason,
      score,
      feedConnected: healthQuery.data?.status === "healthy",
      wsConnected,
    };
  }, [healthQuery.data?.status, recommendation, symbol, wsConnected]);

  const newsSyncedRef = useRef(false);
  const newsFetched = newsQuery.isFetched;
  const calendarFetched = calendarQuery.isFetched;
  const newsEmpty = (newsQuery.data?.length ?? 0) === 0;
  const calendarEmpty = (calendarQuery.data?.length ?? 0) === 0;

  useEffect(() => {
    if (!enabled || newsSyncedRef.current) return;
    if (!newsFetched || !calendarFetched) return;
    if (!newsEmpty && !calendarEmpty) {
      newsSyncedRef.current = true;
      return;
    }
    newsSyncedRef.current = true;
    void syncNewsFeeds()
      .then(() => {
        void queryClient.invalidateQueries({ queryKey: ["news"] });
      })
      .catch(() => {
        /* sync may require admin — ignore */
      });
  }, [
    calendarEmpty,
    calendarFetched,
    enabled,
    newsEmpty,
    newsFetched,
    queryClient,
  ]);

  const newsHeadlines = useMemo(() => {
    const fromNews = newsQuery.data ?? [];
    if (fromNews.length > 0) return fromNews;
    const calendar = calendarQuery.data ?? [];
    const high = calendar.filter((item) => item.impact === "High");
    return high.length > 0 ? high : calendar;
  }, [calendarQuery.data, newsQuery.data]);

  const newsDataUpdatedAt = Math.max(
    newsQuery.dataUpdatedAt ?? 0,
    newsContextQuery.dataUpdatedAt ?? 0,
    calendarQuery.dataUpdatedAt ?? 0,
  );

  const calendarEvents = useMemo(
    () => calendarQuery.data ?? [],
    [calendarQuery.data],
  );

  const scanner: ScannerOpportunity[] = useMemo(() => {
    return scannerQuery.data?.opportunities ?? [];
  }, [scannerQuery.data?.opportunities]);

  const activity: ActivityEvent[] = useMemo(() => {
    const events: ActivityEvent[] = [];

    if (recommendation) {
      events.push({
        id: `rec-${recommendation.id}`,
        title: `New ${recommendation.signal.replace("_", " ")} recommendation`,
        description: `${recommendation.symbol} ${recommendation.timeframe} · confidence ${recommendation.confidence}%`,
        time: relativeTime(recommendation.createdAt),
        tone: "ai",
      });
    }

    if (liveCandle) {
      events.push({
        id: `candle-${liveCandle.time}`,
        title: "Price update",
        description: `${symbol} last ${toNumber(liveCandle.close).toFixed(symbol === "XAUUSD" ? 2 : 5)}`,
        time: relativeTime(String(liveCandle.time)),
        tone: "market",
      });
    }

    if (wsConnected) {
      events.push({
        id: "ws-live",
        title: "Live stream connected",
        description: `Subscribed to ${wsSymbols.length} pairs · ${timeframe}`,
        time: "now",
        tone: "system",
      });
    }

    return events.slice(0, 6);
  }, [
    liveCandle,
    recommendation,
    symbol,
    timeframe,
    wsConnected,
    wsSymbols.length,
  ]);

  return {
    enabled,
    symbol,
    timeframe,
    health: healthQuery.data,
    recommendation,
    timeframeSignals,
    recentRecommendations: historyQuery.data ?? ([] as Recommendation[]),
    newsContext: newsContextQuery.data,
    newsHeadlines,
    calendarEvents,
    newsRefreshing: newsQuery.isFetching || calendarQuery.isFetching,
    newsDataUpdatedAt,
    quotes: quotesQuery.data ?? [],
    watchlist,
    liveCandle,
    scanner,
    activity,
    marketStatus,
    wsConnected,
    isLoading:
      enabled &&
      (scenarioQuery.isLoading ||
        watchlistQuery.isLoading ||
        newsQuery.isLoading),
    isFetching: scenarioQuery.isFetching || watchlistQuery.isFetching,
    error:
      scenarioQuery.error?.message ||
      watchlistQuery.error?.message ||
      null,
    analyze: analyzeMutation.mutateAsync,
    analyzing: analyzeMutation.isPending,
    refetchAll: async () => {
      await Promise.all([
        scenarioQuery.refetch(),
        historyQuery.refetch(),
        watchlistQuery.refetch(),
        scannerQuery.refetch(),
        quotesQuery.refetch(),
        newsQuery.refetch(),
        newsContextQuery.refetch(),
        calendarQuery.refetch(),
        candleQuery.refetch(),
        healthQuery.refetch(),
      ]);
    },
  };
}
