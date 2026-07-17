"use client";

import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MARKET_SYMBOLS, TIMEFRAMES } from "@/constants/markets";
import { getLearningStats } from "@/services/learning";
import { getLatestRecommendation } from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

const STRATEGIES = [
  {
    id: "smc-structure",
    name: "SMC Structure",
    focus: "BOS / CHoCH / order blocks",
    description:
      "Tracks market structure shifts and premium/discount zones before confluence is scored.",
    rules: ["Require structure alignment", "Prefer OB + FVG confluence", "Invalidate on opposing BOS"],
  },
  {
    id: "news-aware",
    name: "News-Aware Momentum",
    focus: "Sentiment + calendar blocks",
    description:
      "Down-weights or blocks entries near high-impact releases; folds news score into confidence.",
    rules: ["Respect NEWS_BLOCK window", "Sentiment must not contradict signal", "High impact → reduce size"],
  },
  {
    id: "mtf-confluence",
    name: "Multi-Timeframe Confluence",
    focus: "HTF bias + LTF trigger",
    description:
      "Higher-timeframe trend sets bias; lower timeframe provides entry timing and RR plan.",
    rules: ["HTF trend filter first", "LTF entry only with RR ≥ target", "Hold/neutral on conflict"],
  },
  {
    id: "adaptive-weights",
    name: "Adaptive Weights",
    focus: "Learning-driven scoring",
    description:
      "Uses labeled outcomes to rebalance confluence weights per symbol and timeframe.",
    rules: ["Retrain on schedule", "Prefer high win-rate patterns", "Decay stale weights"],
  },
];

export function StrategiesView() {
  const user = useAuthStore((s) => s.user);
  const symbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);

  const recommendationQuery = useQuery({
    queryKey: ["recommendation", "latest", symbol, timeframe],
    queryFn: () => getLatestRecommendation(symbol, timeframe),
    enabled: Boolean(user),
    refetchInterval: 60_000,
  });

  const learningQuery = useQuery({
    queryKey: ["learning", "stats", symbol, timeframe],
    queryFn: () => getLearningStats(symbol, timeframe),
    enabled: Boolean(user),
  });

  const activeSignal = recommendationQuery.data?.signal ?? "HOLD";
  const weights = Object.entries(learningQuery.data?.weights ?? {}).slice(0, 6);

  return (
    <div className="mx-auto max-w-[1400px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Strategies
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            Strategy playbook
          </h1>
          <p className="mt-1 text-sm text-muted">
            Athena evaluates confluence — you decide execution
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="ai">Active {activeSignal}</Badge>
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

      <div className="grid gap-3 md:grid-cols-2">
        {STRATEGIES.map((strategy) => (
          <Card key={strategy.id}>
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <CardTitle>{strategy.name}</CardTitle>
                <Badge tone="primary">{strategy.focus}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted">{strategy.description}</p>
              <ul className="space-y-1.5">
                {strategy.rules.map((rule) => (
                  <li key={rule} className="text-xs text-zinc-300">
                    · {rule}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            Live weights · {symbol} {timeframe}
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {weights.length === 0 ? (
            <p className="text-sm text-muted sm:col-span-2 lg:col-span-3">
              Adaptive weights will appear once learning samples exist.
            </p>
          ) : (
            weights.map(([name, value]) => (
              <div
                key={name}
                className="rounded-sm border border-border/60 bg-background/30 px-3 py-2"
              >
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  {name.replace(/_/g, " ")}
                </p>
                <p className="mt-1 font-mono text-lg">{value.toFixed(2)}</p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
