"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { MARKET_SYMBOLS, TIMEFRAMES } from "@/constants/markets";
import { formatPercent } from "@/lib/utils";
import { getLearningStats } from "@/services/learning";
import { getRecommendationHistory } from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

export function AnalyticsView() {
  const user = useAuthStore((s) => s.user);
  const symbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);

  const historyQuery = useQuery({
    queryKey: ["recommendation", "history", symbol, timeframe, 100],
    queryFn: () => getRecommendationHistory(symbol, timeframe, 100),
    enabled: Boolean(user),
    refetchInterval: 60_000,
  });

  const learningQuery = useQuery({
    queryKey: ["learning", "stats", symbol, timeframe],
    queryFn: () => getLearningStats(symbol, timeframe),
    enabled: Boolean(user),
    refetchInterval: 120_000,
  });

  const analytics = useMemo(() => {
    const items = historyQuery.data ?? [];
    const buyish = items.filter((i) => i.signal.includes("BUY")).length;
    const sellish = items.filter((i) => i.signal.includes("SELL")).length;
    const avgConfidence =
      items.length === 0
        ? 0
        : Math.round(items.reduce((sum, i) => sum + i.confidence, 0) / items.length);
    const avgRr =
      items.length === 0
        ? 0
        : items.reduce((sum, i) => sum + i.riskReward, 0) / items.length;
    const highConf = items.filter((i) => i.confidence >= 70).length;
    const distribution = {
      strongBuy: items.filter((i) => i.signal === "STRONG_BUY").length,
      buy: items.filter((i) => i.signal === "BUY").length,
      hold: items.filter((i) => i.signal === "HOLD" || i.signal === "NEUTRAL").length,
      sell: items.filter((i) => i.signal === "SELL").length,
      strongSell: items.filter((i) => i.signal === "STRONG_SELL").length,
    };

    return {
      total: items.length,
      buyish,
      sellish,
      avgConfidence,
      avgRr,
      highConf,
      distribution,
    };
  }, [historyQuery.data]);

  const patternEntries = Object.entries(learningQuery.data?.patternWinRates ?? {}).sort(
    (a, b) => b[1] - a[1],
  );
  const weightEntries = Object.entries(learningQuery.data?.weights ?? {}).sort(
    (a, b) => b[1] - a[1],
  );

  return (
    <div className="mx-auto max-w-[1400px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Analytics
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            Performance intelligence
          </h1>
          <p className="mt-1 text-sm text-muted">
            Recommendation distribution and learning stats for {symbol} {timeframe}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="ai">
            Model{" "}
            {learningQuery.data?.modelAccuracy != null
              ? formatPercent(Math.round(learningQuery.data.modelAccuracy * 100))
              : "n/a"}
          </Badge>
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

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Recommendations" value={`${analytics.total}`} hint="History window" />
        <MetricCard
          label="Avg confidence"
          value={formatPercent(analytics.avgConfidence)}
          hint={`${analytics.highConf} ≥ 70%`}
          tone="ai"
        />
        <MetricCard
          label="Avg RR"
          value={`${analytics.avgRr.toFixed(2)}x`}
          hint="Across stored signals"
          tone="primary"
        />
        <MetricCard
          label="Learning samples"
          value={`${learningQuery.data?.sampleSize ?? 0}`}
          hint="Labeled outcomes"
          tone="bullish"
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Signal distribution</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {(
              [
                ["STRONG BUY", analytics.distribution.strongBuy, "bullish"],
                ["BUY", analytics.distribution.buy, "bullish"],
                ["HOLD / NEUTRAL", analytics.distribution.hold, "neutral"],
                ["SELL", analytics.distribution.sell, "bearish"],
                ["STRONG SELL", analytics.distribution.strongSell, "bearish"],
              ] as const
            ).map(([label, count, tone]) => {
              const pct = analytics.total ? Math.round((count / analytics.total) * 100) : 0;
              return (
                <div key={label}>
                  <div className="mb-1 flex justify-between text-xs">
                    <span className="text-muted">{label}</span>
                    <span className="font-mono">
                      {count} · {pct}%
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-sm bg-background/50">
                    <div
                      className={
                        tone === "bullish"
                          ? "h-full bg-bullish/70"
                          : tone === "bearish"
                            ? "h-full bg-bearish/70"
                            : "h-full bg-zinc-500/70"
                      }
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
            <p className="pt-2 text-xs text-muted">
              Bias mix: {analytics.buyish} buy-side · {analytics.sellish} sell-side
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pattern win rates</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {patternEntries.length === 0 ? (
              <p className="text-sm text-muted">
                No labeled pattern stats yet. Outcomes populate as trades resolve.
              </p>
            ) : (
              patternEntries.slice(0, 8).map(([name, rate]) => (
                <div
                  key={name}
                  className="flex items-center justify-between rounded-sm border border-border/60 px-3 py-2 text-sm"
                >
                  <span className="capitalize text-zinc-200">{name.replace(/_/g, " ")}</span>
                  <span className="font-mono tabular-nums">
                    {formatPercent(Math.round(rate * (rate <= 1 ? 100 : 1)))}
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Adaptive confluence weights</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {weightEntries.length === 0 ? (
              <p className="text-sm text-muted sm:col-span-2 lg:col-span-3">
                Weights unavailable for this symbol/timeframe.
              </p>
            ) : (
              weightEntries.map(([name, weight]) => (
                <div
                  key={name}
                  className="rounded-sm border border-border/60 bg-background/30 px-3 py-2"
                >
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                    {name.replace(/_/g, " ")}
                  </p>
                  <p className="mt-1 font-mono text-lg tabular-nums">
                    {weight.toFixed(2)}
                  </p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
