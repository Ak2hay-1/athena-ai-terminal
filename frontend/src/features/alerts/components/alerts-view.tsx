"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bell, Newspaper, ShieldAlert, TrendingUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MARKET_SYMBOLS, TIMEFRAMES } from "@/constants/markets";
import { currentSession, relativeTime } from "@/lib/mappers";
import { formatPercent } from "@/lib/utils";
import { getCalendar, getLatestNews, getNewsContext } from "@/services/news";
import {
  getLatestRecommendation,
  getRecommendationHistory,
} from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

type AlertItem = {
  id: string;
  title: string;
  detail: string;
  time: string;
  severity: "high" | "medium" | "info";
  kind: "news" | "signal" | "session" | "structure";
};

export function AlertsView() {
  const user = useAuthStore((s) => s.user);
  const symbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);

  const newsContextQuery = useQuery({
    queryKey: ["news", "context", symbol],
    queryFn: () => getNewsContext(symbol),
    enabled: Boolean(user),
    refetchInterval: 30_000,
  });

  const newsQuery = useQuery({
    queryKey: ["news", "latest", symbol, "alerts"],
    queryFn: () => getLatestNews(symbol, 10),
    enabled: Boolean(user),
    refetchInterval: 30_000,
  });

  const calendarQuery = useQuery({
    queryKey: ["news", "calendar", "alerts"],
    queryFn: () => getCalendar(12),
    enabled: Boolean(user),
    refetchInterval: 60_000,
  });

  const recommendationQuery = useQuery({
    queryKey: ["recommendation", "latest", symbol, timeframe],
    queryFn: () => getLatestRecommendation(symbol, timeframe),
    enabled: Boolean(user),
    refetchInterval: 30_000,
  });

  const historyQuery = useQuery({
    queryKey: ["recommendation", "history", symbol, timeframe, 5],
    queryFn: () => getRecommendationHistory(symbol, timeframe, 5),
    enabled: Boolean(user),
    refetchInterval: 60_000,
  });

  const alerts = useMemo(() => {
    const items: AlertItem[] = [];
    const context = newsContextQuery.data;
    const recommendation = recommendationQuery.data;
    const history = historyQuery.data ?? [];

    if (context?.highImpactUpcoming) {
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
          detail: `${item.symbols.join(", ") || symbol} · ${item.impact} impact`,
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

    if (recommendation && recommendation.confidence >= 70) {
      items.push({
        id: `sig-${recommendation.id}`,
        title: `${recommendation.signal} confidence shift`,
        detail: `${symbol} ${timeframe} at ${formatPercent(recommendation.confidence)} · ${recommendation.trend}`,
        time: relativeTime(recommendation.createdAt),
        severity: recommendation.confidence >= 80 ? "high" : "medium",
        kind: "signal",
      });
    }

    if (history.length >= 2) {
      const [latest, previous] = history;
      if (latest.signal !== previous.signal) {
        items.push({
          id: "signal-flip",
          title: "Signal flipped",
          detail: `${previous.signal} → ${latest.signal} on ${symbol} ${timeframe}`,
          time: relativeTime(latest.createdAt),
          severity: "medium",
          kind: "structure",
        });
      }
    }

    items.push({
      id: "session",
      title: `${currentSession()} session active`,
      detail: "Session volatility context for alert routing",
      time: "live",
      severity: "info",
      kind: "session",
    });

    return items;
  }, [
    calendarQuery.data,
    historyQuery.data,
    newsContextQuery.data,
    newsQuery.data,
    recommendationQuery.data,
    symbol,
    timeframe,
  ]);

  const iconFor = (kind: AlertItem["kind"]) => {
    if (kind === "news") return Newspaper;
    if (kind === "signal") return TrendingUp;
    if (kind === "structure") return ShieldAlert;
    return Bell;
  };

  return (
    <div className="mx-auto max-w-[1100px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Alerts
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            Intelligence alerts
          </h1>
          <p className="mt-1 text-sm text-muted">
            News impact, confidence shifts, and session context — not broker fills
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="warning">{alerts.filter((a) => a.severity === "high").length} high</Badge>
          <select
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
            className="h-9 rounded-sm border border-border bg-panel px-3 font-mono text-sm outline-none focus:border-primary/50"
          >
            {MARKET_SYMBOLS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select
            value={timeframe}
            onChange={(event) => setTimeframe(event.target.value)}
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

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>{alerts.length} active alerts</CardTitle>
          <Badge tone="bullish">Realtime poll</Badge>
        </CardHeader>
        <CardContent className="space-y-2">
          {alerts.map((alert) => {
            const Icon = iconFor(alert.kind);
            return (
              <div
                key={alert.id}
                className="flex gap-3 rounded-sm border border-border/70 bg-background/30 px-3 py-3"
              >
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border border-border bg-panel">
                  <Icon className="h-3.5 w-3.5 text-primary" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-medium">{alert.title}</p>
                    <div className="flex items-center gap-2">
                      <Badge
                        tone={
                          alert.severity === "high"
                            ? "warning"
                            : alert.severity === "medium"
                              ? "primary"
                              : "neutral"
                        }
                      >
                        {alert.severity}
                      </Badge>
                      <span className="text-[11px] text-muted">{alert.time}</span>
                    </div>
                  </div>
                  <p className="mt-1 text-xs text-muted">{alert.detail}</p>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
