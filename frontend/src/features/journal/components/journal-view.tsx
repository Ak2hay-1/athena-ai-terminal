"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SignalBadge } from "@/components/ui/signal-badge";
import { MARKET_SYMBOLS, TIMEFRAMES, priceDigitsFor } from "@/constants/markets";
import { relativeTime } from "@/lib/mappers";
import { cn, formatPercent, formatPrice } from "@/lib/utils";
import { getRecommendationHistory } from "@/services/recommendations";
import { getPositions } from "@/services/trading";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

export function JournalView() {
  const user = useAuthStore((s) => s.user);
  const symbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);

  const historyQuery = useQuery({
    queryKey: ["recommendation", "history", symbol, timeframe, 30],
    queryFn: () => getRecommendationHistory(symbol, timeframe, 30),
    enabled: Boolean(user),
    refetchInterval: 60_000,
  });

  const positionsQuery = useQuery({
    queryKey: ["trade", "positions"],
    queryFn: getPositions,
    enabled: Boolean(user),
    refetchInterval: 20_000,
  });

  const entries = useMemo(() => {
    const fromRecs = (historyQuery.data ?? []).map((item) => ({
      id: `rec-${item.id}`,
      kind: "recommendation" as const,
      title: `${item.symbol} ${item.signal}`,
      subtitle: `${item.timeframe} · ${formatPercent(item.confidence)} · ${item.risk} risk`,
      body:
        item.reasons.slice(0, 3).join(" · ") ||
        `${item.trend} bias with RR ${item.riskReward.toFixed(1)}x`,
      time: relativeTime(item.createdAt),
      href: `/recommendations/${item.id}`,
      signal: item.signal,
      tone: item.signal.includes("BUY")
        ? "bullish"
        : item.signal.includes("SELL")
          ? "bearish"
          : "neutral",
    }));

    const fromPositions = (positionsQuery.data ?? []).map((position) => {
      const digits = priceDigitsFor(position.symbol, position.entry);
      return {
        id: `pos-${position.id}`,
        kind: "trade" as const,
        title: `${position.symbol} ${position.side}`,
        subtitle: `${position.status} · vol ${position.volume}`,
        body: `Entry ${formatPrice(position.entry, digits)} · SL ${formatPrice(position.stopLoss, digits)} · TP ${formatPrice(position.takeProfit, digits)} · PnL ${position.pnl.toFixed(2)}`,
        time: "live",
        href: `/markets/${position.symbol.toLowerCase()}`,
        signal: position.side === "BUY" ? ("BUY" as const) : ("SELL" as const),
        tone: position.pnl >= 0 ? "bullish" : "bearish",
      };
    });

    return [...fromPositions, ...fromRecs];
  }, [historyQuery.data, positionsQuery.data]);

  return (
    <div className="mx-auto max-w-[1100px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Journal
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Trading journal</h1>
          <p className="mt-1 text-sm text-muted">
            Linked recommendations and open positions for review
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

      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-5">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Entries</p>
            <p className="mt-1 font-mono text-2xl">{entries.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
              Open positions
            </p>
            <p className="mt-1 font-mono text-2xl">
              {(positionsQuery.data ?? []).filter((p) => p.status === "open").length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
              Recommendations
            </p>
            <p className="mt-1 font-mono text-2xl">{historyQuery.data?.length ?? 0}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent notes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {entries.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted">
              Journal is empty — run analysis or open a paper trade to start logging.
            </p>
          ) : (
            entries.map((entry) => (
              <Link
                key={entry.id}
                href={entry.href}
                className="block rounded-sm border border-border/70 bg-background/30 px-3 py-3 transition-colors hover:border-primary/30"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <SignalBadge signal={entry.signal} />
                    <Badge tone={entry.kind === "trade" ? "primary" : "ai"}>
                      {entry.kind}
                    </Badge>
                    <p className="text-sm font-medium">{entry.title}</p>
                  </div>
                  <span className="text-[11px] text-muted">{entry.time}</span>
                </div>
                <p className="mt-1 text-xs text-muted">{entry.subtitle}</p>
                <p
                  className={cn(
                    "mt-2 text-sm",
                    entry.tone === "bullish"
                      ? "text-bullish"
                      : entry.tone === "bearish"
                        ? "text-bearish"
                        : "text-zinc-300",
                  )}
                >
                  {entry.body}
                </p>
              </Link>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
