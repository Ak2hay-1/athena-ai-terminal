"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { currentSession, relativeTime } from "@/lib/mappers";
import { formatPercent } from "@/lib/utils";
import { getCalendar, getLatestNews, getNewsContext } from "@/services/news";
import {
  getLatestRecommendation,
  getRecommendationHistory,
} from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

export type AlertItem = {
  id: string;
  title: string;
  detail: string;
  time: string;
  severity: "high" | "medium" | "info";
  kind: "news" | "signal" | "session" | "structure";
};

export function useDerivedAlerts(options?: {
  symbolFilter?: string;
  enabled?: boolean;
}) {
  const user = useAuthStore((s) => s.user);
  const storeSymbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);

  const [internalSymbolFilter, setInternalSymbolFilter] = useState(
    options?.symbolFilter ?? storeSymbol,
  );
  const symbolFilter = options?.symbolFilter ?? internalSymbolFilter;
  const setSymbolFilter = setInternalSymbolFilter;

  const enabled = (options?.enabled ?? true) && Boolean(user);
  const isAll = symbolFilter === "ALL";
  const historySymbol = isAll ? null : symbolFilter;

  const newsContextQuery = useQuery({
    queryKey: ["news", "context", symbolFilter],
    queryFn: () => getNewsContext(symbolFilter),
    enabled: enabled && !isAll,
    refetchInterval: 30_000,
  });

  const newsQuery = useQuery({
    queryKey: ["news", "latest", isAll ? "ALL" : symbolFilter, "alerts"],
    queryFn: () => getLatestNews(isAll ? "XAUUSD" : symbolFilter, 10),
    enabled,
    refetchInterval: 30_000,
  });

  const calendarQuery = useQuery({
    queryKey: ["news", "calendar", "alerts"],
    queryFn: () => getCalendar(12),
    enabled,
    refetchInterval: 60_000,
  });

  const recommendationQuery = useQuery({
    queryKey: ["recommendation", "latest", symbolFilter, timeframe],
    queryFn: () => getLatestRecommendation(symbolFilter, timeframe),
    enabled: enabled && !isAll,
    refetchInterval: 30_000,
  });

  const historyQuery = useQuery({
    queryKey: [
      "recommendation",
      "history",
      symbolFilter,
      timeframe,
      isAll ? 20 : 5,
    ],
    queryFn: () =>
      getRecommendationHistory(historySymbol, timeframe, isAll ? 20 : 5),
    enabled,
    refetchInterval: 60_000,
  });

  const alerts = useMemo(() => {
    const items: AlertItem[] = [];
    const context = newsContextQuery.data;
    const recommendation = recommendationQuery.data;
    const history = historyQuery.data ?? [];

    if (!isAll && context?.highImpactUpcoming) {
      const next = context.upcomingEvents?.[0];
      items.push({
        id: "news-window",
        title: "High-impact news window",
        detail: next
          ? `${next.title} · ${next.impact} impact approaching`
          : "Elevated event risk for the current symbol",
        time: "now",
        severity: "high",
        kind: "news",
      });
    }

    (newsQuery.data ?? [])
      .filter((item) => item.impact === "High")
      .slice(0, 4)
      .forEach((item) => {
        items.push({
          id: `news-${item.id}`,
          title: item.title,
          detail: `${item.symbols.join(", ") || (isAll ? "market" : symbolFilter)} · ${item.impact} impact`,
          time: item.time,
          severity: "high",
          kind: "news",
        });
      });

    (calendarQuery.data ?? [])
      .filter((item) => item.impact === "High")
      .slice(0, 3)
      .forEach((item) => {
        items.push({
          id: `cal-${item.id}`,
          title: `Calendar: ${item.title}`,
          detail: "Economic release on watchlist",
          time: item.time,
          severity: "medium",
          kind: "news",
        });
      });

    if (!isAll && recommendation && recommendation.confidence >= 70) {
      items.push({
        id: `sig-${recommendation.id}`,
        title: `${recommendation.signal} confidence shift`,
        detail: `${symbolFilter} ${timeframe} at ${formatPercent(recommendation.confidence)} · ${recommendation.trend}`,
        time: relativeTime(recommendation.createdAt),
        severity: recommendation.confidence >= 80 ? "high" : "medium",
        kind: "signal",
      });
    }

    if (isAll) {
      history
        .filter((item) => item.confidence >= 70)
        .slice(0, 5)
        .forEach((item) => {
          items.push({
            id: `sig-all-${item.id}`,
            title: `${item.symbol} ${item.signal}`,
            detail: `${item.timeframe} at ${formatPercent(item.confidence)} · ${item.trend}`,
            time: relativeTime(item.createdAt),
            severity: item.confidence >= 80 ? "high" : "medium",
            kind: "signal",
          });
        });

      const bySymbol = new Map<string, typeof history>();
      for (const item of history) {
        const list = bySymbol.get(item.symbol) ?? [];
        list.push(item);
        bySymbol.set(item.symbol, list);
      }
      for (const [sym, rows] of bySymbol) {
        if (rows.length < 2) continue;
        const [latest, previous] = rows;
        if (latest.signal !== previous.signal) {
          items.push({
            id: `signal-flip-${sym}`,
            title: `Signal flipped · ${sym}`,
            detail: `${previous.signal} → ${latest.signal} on ${sym} ${timeframe}`,
            time: relativeTime(latest.createdAt),
            severity: "medium",
            kind: "structure",
          });
        }
      }
    } else if (history.length >= 2) {
      const [latest, previous] = history;
      if (latest.signal !== previous.signal) {
        items.push({
          id: "signal-flip",
          title: "Signal flipped",
          detail: `${previous.signal} → ${latest.signal} on ${symbolFilter} ${timeframe}`,
          time: relativeTime(latest.createdAt),
          severity: "medium",
          kind: "structure",
        });
      }
    }

    items.push({
      id: "session",
      title: `${currentSession()} session active`,
      detail: isAll
        ? "Session volatility context across all pairs"
        : "Session volatility context for alert routing",
      time: "live",
      severity: "info",
      kind: "session",
    });

    return items;
  }, [
    calendarQuery.data,
    historyQuery.data,
    isAll,
    newsContextQuery.data,
    newsQuery.data,
    recommendationQuery.data,
    symbolFilter,
    timeframe,
  ]);

  const highCount = alerts.filter((a) => a.severity === "high").length;

  return {
    alerts,
    highCount,
    symbolFilter,
    setSymbolFilter,
    timeframe,
    setSymbol,
    setTimeframe,
    isAll,
  };
}
