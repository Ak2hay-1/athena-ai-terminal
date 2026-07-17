"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SignalBadge } from "@/components/ui/signal-badge";
import { MARKET_SYMBOLS, TIMEFRAMES, priceDigitsFor } from "@/constants/markets";
import { relativeTime } from "@/lib/mappers";
import { cn, formatPercent, formatPrice } from "@/lib/utils";
import { getRecommendationHistory } from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";
import type { Signal } from "@/types";

const SIGNAL_FILTERS: Array<"ALL" | Signal> = [
  "ALL",
  "STRONG_BUY",
  "BUY",
  "SELL",
  "STRONG_SELL",
  "HOLD",
  "NO_TRADE",
  "NEUTRAL",
];

export function HistoryView() {
  const user = useAuthStore((s) => s.user);
  const symbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);
  const [signalFilter, setSignalFilter] = useState<(typeof SIGNAL_FILTERS)[number]>("ALL");
  const [minConfidence, setMinConfidence] = useState(0);

  const historyQuery = useQuery({
    queryKey: ["recommendation", "history", symbol, timeframe, 50],
    queryFn: () => getRecommendationHistory(symbol, timeframe, 50),
    enabled: Boolean(user),
    refetchInterval: 60_000,
  });

  const rows = useMemo(() => {
    return (historyQuery.data ?? [])
      .filter((item) => (signalFilter === "ALL" ? true : item.signal === signalFilter))
      .filter((item) => item.confidence >= minConfidence);
  }, [historyQuery.data, minConfidence, signalFilter]);

  return (
    <div className="mx-auto max-w-[1400px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            History
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            Recommendation history
          </h1>
          <p className="mt-1 text-sm text-muted">
            Filterable timeline for {symbol} {timeframe}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
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
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {SIGNAL_FILTERS.map((signal) => (
            <button
              key={signal}
              type="button"
              onClick={() => setSignalFilter(signal)}
              className={cn(
                "rounded-sm border px-2.5 py-1 text-[11px] uppercase tracking-wide",
                signalFilter === signal
                  ? "border-primary bg-primary/15 text-primary"
                  : "border-border text-muted hover:text-foreground",
              )}
            >
              {signal.replace("_", " ")}
            </button>
          ))}
          <label className="ml-auto flex items-center gap-2 text-xs text-muted">
            Min conf
            <input
              type="range"
              min={0}
              max={90}
              step={5}
              value={minConfidence}
              onChange={(event) => setMinConfidence(Number(event.target.value))}
              className="accent-primary"
            />
            <span className="font-mono text-foreground">{minConfidence}</span>
          </label>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>{rows.length} recommendations</CardTitle>
          <Badge tone="primary">{historyQuery.isFetching ? "Refreshing" : "Live"}</Badge>
        </CardHeader>
        <CardContent className="space-y-2">
          {historyQuery.isLoading ? (
            <p className="py-8 text-center text-sm text-muted">Loading history…</p>
          ) : null}
          {!historyQuery.isLoading && rows.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted">
              No recommendations match these filters.
            </p>
          ) : null}
          {rows.map((item) => {
            const digits = priceDigitsFor(item.symbol, item.entry);
            return (
              <Link
                key={item.id}
                href={`/recommendations/${item.id}`}
                className="flex flex-wrap items-center justify-between gap-3 rounded-sm border border-border/70 bg-background/30 px-3 py-3 transition-colors hover:border-primary/30 hover:bg-primary/5"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-mono text-sm font-semibold">
                      {item.symbol} · {item.timeframe}
                    </p>
                    <SignalBadge signal={item.signal} />
                    <Badge tone="default">{item.risk} risk</Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted">
                    Entry {formatPrice(item.entry, digits)} · SL{" "}
                    {formatPrice(item.stopLoss, digits)} · TP{" "}
                    {formatPrice(item.takeProfit, digits)} · RR{" "}
                    {item.riskReward.toFixed(1)}x
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm tabular-nums">
                    {formatPercent(item.confidence)}
                  </p>
                  <p className="text-[11px] text-muted">
                    {relativeTime(item.createdAt)}
                  </p>
                </div>
              </Link>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
