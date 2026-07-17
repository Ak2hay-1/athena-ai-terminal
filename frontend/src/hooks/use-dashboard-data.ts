"use client";

import { useCallback, useMemo } from "react";
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
import { applyQuoteToCandle } from "@/lib/utils";
import { getHealth } from "@/services/health";
import { getCandles, getLatestCandle, getQuotes } from "@/services/market";
import { getCalendar, getLatestNews, getNewsContext } from "@/services/news";
import {
  analyzeMarket,
  getLatestRecommendation,
  getRecommendationHistory,
} from "@/services/recommendations";
import { getPositions } from "@/services/trading";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";
import type {
  ActivityEvent,
  Candle,
  MarketStatus,
  Recommendation,
  ScannerOpportunity,
  WatchlistItem,
} from "@/types";
import { useMarketWebSocket } from "./use-market-websocket";

const WATCHLIST_SYMBOLS = [...MARKET_SYMBOLS];

async function buildWatchlist(timeframe: string): Promise<WatchlistItem[]> {
  const [rows, quotes] = await Promise.all([
    Promise.all(
      WATCHLIST_SYMBOLS.map(async (symbol) => {
        const [recommendation, candles] = await Promise.all([
          getLatestRecommendation(symbol, timeframe),
          getCandles(symbol, timeframe, 3),
        ]);

        const latest = candles.at(-1);
        const previous = candles.at(-2);
        const referencePrice = previous?.close ?? latest?.close ?? recommendation?.entry ?? 0;
        const price = latest?.close ?? recommendation?.entry ?? 0;
        const changePercent =
          price && referencePrice
            ? ((price - referencePrice) / referencePrice) * 100
            : 0;

        return {
          symbol,
          price,
          referencePrice,
          changePercent,
          signal: recommendation?.signal ?? "HOLD",
          confidence: recommendation?.confidence ?? 0,
          trend: recommendation?.trend ?? "Neutral",
        } satisfies WatchlistItem;
      }),
    ),
    getQuotes([...WATCHLIST_SYMBOLS], timeframe),
  ]);

  const quoteMap = new Map(quotes.map((q) => [q.symbol.toUpperCase(), q.mid]));

  return rows.map((row) => {
    const live = quoteMap.get(row.symbol);
    if (live == null || live === 0) return row;
    const reference = row.referencePrice || row.price || live;
    return {
      ...row,
      price: live,
      changePercent:
        reference > 0 ? ((live - reference) / reference) * 100 : row.changePercent,
    };
  });
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

  const recommendationQuery = useQuery({
    queryKey: ["recommendation", "latest", symbol, timeframe],
    queryFn: () => getLatestRecommendation(symbol, timeframe),
    enabled,
    refetchInterval: 60_000,
  });

  const historyQuery = useQuery({
    queryKey: ["recommendation", "history", symbol, timeframe],
    queryFn: () => getRecommendationHistory(symbol, timeframe, 8),
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

  const positionsQuery = useQuery({
    queryKey: ["trade", "positions"],
    queryFn: getPositions,
    enabled,
    refetchInterval: 20_000,
  });

  const candleQuery = useQuery({
    queryKey: ["market", "latest", symbol, timeframe],
    queryFn: () => getLatestCandle(symbol, timeframe),
    enabled,
    refetchInterval: 15_000,
  });

  const candlesQuery = useQuery({
    queryKey: ["market", "candles", symbol, timeframe],
    queryFn: () => getCandles(symbol, timeframe, 200),
    enabled,
    refetchInterval: 60_000,
  });

  const watchlistQuery = useQuery({
    queryKey: ["watchlist", "live", timeframe],
    queryFn: () => buildWatchlist(timeframe),
    enabled,
    refetchInterval: 45_000,
  });

  const quotesQuery = useQuery({
    queryKey: ["market", "quotes", [...WATCHLIST_SYMBOLS].join(","), timeframe],
    queryFn: () => getQuotes([...WATCHLIST_SYMBOLS], timeframe),
    enabled,
    refetchInterval: 1_000,
    staleTime: 500,
  });

  const analyzeMutation = useMutation({
    mutationFn: () => analyzeMarket(symbol, timeframe),
    onSuccess: (result) => {
      if (result.recommendation) {
        queryClient.setQueryData(
          ["recommendation", "latest", symbol, timeframe],
          result.recommendation,
        );
      }
      void queryClient.invalidateQueries({
        queryKey: ["recommendation", "history", symbol, timeframe],
      });
      void queryClient.invalidateQueries({ queryKey: ["watchlist", "live", timeframe] });
    },
  });

  const patchWatchlistPrice = useCallback(
    (targetSymbol: string, price: number, extras?: Partial<WatchlistItem>) => {
      if (!price) return;
      queryClient.setQueryData<WatchlistItem[]>(
        ["watchlist", "live", timeframe],
        (current) => {
          if (!current) return current;
          return current.map((item) => {
            if (item.symbol !== targetSymbol) return item;
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
    [queryClient, timeframe],
  );

  const onWsMessage = useCallback(
    (payload: Record<string, unknown>) => {
      if (payload.type !== "candle_update") return;

      const updateSymbol = String(payload.symbol ?? "").toUpperCase();
      const updateTf = String(payload.timeframe ?? "").toUpperCase();
      if (!updateSymbol || updateTf !== timeframe.toUpperCase()) return;

      const candleRaw = payload.candle as Record<string, unknown> | undefined;
      const mappedCandle = candleRaw
        ? mapCandle(candleRaw, { symbol: updateSymbol, timeframe: updateTf })
        : null;

      if (mappedCandle) {
        patchWatchlistPrice(updateSymbol, mappedCandle.close);

        if (updateSymbol === symbol.toUpperCase()) {
          queryClient.setQueryData(
            ["market", "latest", symbol, timeframe],
            mappedCandle,
          );
          queryClient.setQueryData<Candle[]>(
            ["market", "candles", symbol, timeframe],
            (current) => {
              if (!current || current.length === 0) return [mappedCandle];
              const next = [...current];
              const last = next[next.length - 1];
              if (last && last.time === mappedCandle.time) {
                next[next.length - 1] = mappedCandle;
              } else {
                next.push(mappedCandle);
                if (next.length > 300) next.shift();
              }
              return next;
            },
          );
        }
      }

      if (payload.recommendation && updateSymbol === symbol.toUpperCase()) {
        const mapped = mapRecommendation(
          payload.recommendation as Record<string, unknown>,
          { symbol, timeframe },
        );
        if (mapped) {
          queryClient.setQueryData(
            ["recommendation", "latest", symbol, timeframe],
            mapped,
          );
          patchWatchlistPrice(updateSymbol, mapped.entry || mappedCandle?.close || 0, {
            signal: mapped.signal,
            confidence: mapped.confidence,
            trend: mapped.trend,
          });
        }
      } else if (payload.recommendation) {
        const rec = payload.recommendation as Record<string, unknown>;
        patchWatchlistPrice(
          updateSymbol,
          toNumber(rec.entry) || mappedCandle?.close || 0,
          {
            signal: normalizeSignal(rec.signal),
            confidence: Math.round(toNumber(rec.confidence)),
            trend: normalizeTrend(rec.trend),
          },
        );
      }
    },
    [patchWatchlistPrice, queryClient, symbol, timeframe],
  );

  const { connected: wsConnected } = useMarketWebSocket({
    symbols: [...WATCHLIST_SYMBOLS],
    timeframe,
    onMessage: onWsMessage,
    enabled,
  });

  // Merge fast quote poll into watchlist so all pairs tick live
  const watchlist = useMemo(() => {
    const base = watchlistQuery.data ?? [];
    const quotes = quotesQuery.data ?? [];
    if (base.length === 0 || quotes.length === 0) return base;

    const quoteMap = new Map(
      quotes.map((q) => [q.symbol.toUpperCase(), q.mid] as const),
    );

    return base.map((item) => {
      const mid = quoteMap.get(item.symbol);
      if (mid == null || mid === 0) return item;
      const reference = item.referencePrice || item.price || mid;
      return {
        ...item,
        price: mid,
        changePercent:
          reference > 0 ? ((mid - reference) / reference) * 100 : item.changePercent,
      };
    });
  }, [quotesQuery.data, watchlistQuery.data]);

  const recommendation = recommendationQuery.data ?? null;
  const candles = candlesQuery.data ?? [];
  const quoteMid =
    quotesQuery.data?.find((q) => q.symbol.toUpperCase() === symbol.toUpperCase())
      ?.mid ?? 0;

  const baseLiveCandle = candleQuery.data ?? candles.at(-1) ?? null;
  const liveCandle =
    baseLiveCandle && quoteMid
      ? applyQuoteToCandle(baseLiveCandle, quoteMid)
      : baseLiveCandle;

  const marketStatus: MarketStatus = useMemo(() => {
    const score = recommendation?.confluence ?? recommendation?.confidence ?? 0;
    const volatility: MarketStatus["volatility"] =
      score >= 80 ? "High" : score >= 55 ? "Medium" : "Low";

    return {
      session: currentSession(),
      volatility,
      marketOpen: healthQuery.data?.status === "healthy",
      score,
      feedConnected: healthQuery.data?.status === "healthy",
      wsConnected,
    };
  }, [healthQuery.data?.status, recommendation, wsConnected]);

  const newsHeadlines = useMemo(() => {
    const fromNews = newsQuery.data ?? [];
    if (fromNews.length > 0) return fromNews;
    return (calendarQuery.data ?? []).filter((item) => item.impact === "High");
  }, [calendarQuery.data, newsQuery.data]);

  const calendarEvents = useMemo(
    () => calendarQuery.data ?? [],
    [calendarQuery.data],
  );

  const scanner: ScannerOpportunity[] = useMemo(() => {
    return watchlist
      .map((item) => {
        const changeAbs = Math.abs(item.changePercent);
        const momentumBoost = Math.min(20, Math.round(changeAbs * 8));
        const score = Math.min(99, item.confidence + momentumBoost);
        return {
          id: `${item.symbol}-${timeframe}`,
          symbol: item.symbol,
          signal: item.signal,
          confidence: score,
          timeframe,
          session: marketStatus.session,
          reason:
            item.signal !== "HOLD"
              ? `${item.trend} · ${item.changePercent >= 0 ? "+" : ""}${item.changePercent.toFixed(2)}% · live`
              : `${item.trend} · scanning momentum`,
          price: item.price,
          changePercent: item.changePercent,
        };
      })
      .filter((item) => item.confidence >= 45 || item.signal !== "HOLD")
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 12);
  }, [marketStatus.session, timeframe, watchlist]);

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
        description: `Subscribed to ${WATCHLIST_SYMBOLS.length} pairs · ${timeframe}`,
        time: "now",
        tone: "system",
      });
    }

    (positionsQuery.data ?? []).slice(0, 2).forEach((position) => {
      events.push({
        id: `pos-${position.id}`,
        title: "Open position",
        description: `${position.symbol} ${position.side}`,
        time: "live",
        tone: "trade",
      });
    });

    return events.slice(0, 6);
  }, [
    liveCandle,
    positionsQuery.data,
    recommendation,
    symbol,
    timeframe,
    wsConnected,
  ]);

  return {
    enabled,
    symbol,
    timeframe,
    health: healthQuery.data,
    recommendation,
    recentRecommendations: historyQuery.data ?? ([] as Recommendation[]),
    newsContext: newsContextQuery.data,
    newsHeadlines,
    calendarEvents,
    newsRefreshing: newsQuery.isFetching || calendarQuery.isFetching,
    positions: positionsQuery.data ?? [],
    watchlist,
    candles,
    liveCandle,
    scanner,
    activity,
    marketStatus,
    wsConnected,
    isLoading:
      enabled &&
      (recommendationQuery.isLoading ||
        watchlistQuery.isLoading ||
        newsQuery.isLoading),
    isFetching: recommendationQuery.isFetching || watchlistQuery.isFetching,
    error:
      recommendationQuery.error?.message ||
      watchlistQuery.error?.message ||
      null,
    analyze: analyzeMutation.mutateAsync,
    analyzing: analyzeMutation.isPending,
    refetchAll: async () => {
      await Promise.all([
        recommendationQuery.refetch(),
        historyQuery.refetch(),
        watchlistQuery.refetch(),
        quotesQuery.refetch(),
        newsQuery.refetch(),
        newsContextQuery.refetch(),
        calendarQuery.refetch(),
        positionsQuery.refetch(),
        candleQuery.refetch(),
        candlesQuery.refetch(),
        healthQuery.refetch(),
      ]);
    },
  };
}
