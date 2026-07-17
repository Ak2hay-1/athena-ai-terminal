"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SignalBadge } from "@/components/ui/signal-badge";
import {
  MARKET_CATEGORIES,
  TIMEFRAMES,
  priceDigitsFor,
  symbolCategory,
} from "@/constants/markets";
import { useDashboardData } from "@/hooks/use-dashboard-data";
import { cn, formatPercent, formatPrice } from "@/lib/utils";
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
];

export function ScannerView() {
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);
  const {
    timeframe,
    scanner,
    watchlist,
    wsConnected,
    marketStatus,
    isLoading,
  } = useDashboardData();

  const [signalFilter, setSignalFilter] = useState<(typeof SIGNAL_FILTERS)[number]>("ALL");
  const [categoryFilter, setCategoryFilter] = useState<"all" | "metals" | "forex" | "crypto">(
    "all",
  );
  const [minConfidence, setMinConfidence] = useState(40);

  const rows = useMemo(() => {
    const base =
      scanner.length > 0
        ? scanner
        : watchlist.map((item) => ({
            id: `${item.symbol}-${timeframe}`,
            symbol: item.symbol,
            signal: item.signal,
            confidence: item.confidence,
            timeframe,
            session: marketStatus.session,
            reason: `${item.trend} · live watchlist`,
            price: item.price,
            changePercent: item.changePercent,
          }));

    return base
      .filter((item) => (signalFilter === "ALL" ? true : item.signal === signalFilter))
      .filter((item) =>
        categoryFilter === "all"
          ? true
          : symbolCategory(item.symbol) === categoryFilter,
      )
      .filter((item) => item.confidence >= minConfidence)
      .sort((a, b) => b.confidence - a.confidence);
  }, [categoryFilter, marketStatus.session, minConfidence, scanner, signalFilter, timeframe, watchlist]);

  return (
    <div className="mx-auto max-w-[1400px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Intelligence
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Market Scanner</h1>
          <p className="mt-1 text-sm text-muted">
            Ranked opportunities across FX, metals, and crypto · {marketStatus.session} session
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={wsConnected ? "bullish" : "warning"}>
            {wsConnected ? "Live stream" : "Live quotes"}
          </Badge>
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
          {(["all", "metals", "forex", "crypto"] as const).map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setCategoryFilter(cat)}
              className={cn(
                "rounded-sm border px-2.5 py-1 text-[11px] uppercase tracking-wide",
                categoryFilter === cat
                  ? "border-primary bg-primary/15 text-primary"
                  : "border-border text-muted hover:text-foreground",
              )}
            >
              {cat}
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

      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
        {isLoading && rows.length === 0 ? (
          <Card className="sm:col-span-2 xl:col-span-3">
            <CardContent className="py-10 text-center text-sm text-muted">
              Scanning markets…
            </CardContent>
          </Card>
        ) : null}

        {!isLoading && rows.length === 0 ? (
          <Card className="sm:col-span-2 xl:col-span-3">
            <CardContent className="py-10 text-center text-sm text-muted">
              No opportunities match the current filters.
            </CardContent>
          </Card>
        ) : null}

        {rows.map((item) => {
          const digits = priceDigitsFor(item.symbol, item.price ?? 0);
          const category = symbolCategory(item.symbol);
          const inCrypto = (MARKET_CATEGORIES.crypto as readonly string[]).includes(
            item.symbol,
          );
          return (
            <Link key={item.id} href={`/markets/${item.symbol.toLowerCase()}`}>
              <Card className="h-full transition-colors hover:border-primary/40">
                <CardContent className="space-y-3 pt-5">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-mono text-base font-semibold tracking-wide">
                        {item.symbol}
                      </p>
                      <p className="mt-0.5 text-[11px] uppercase tracking-wide text-muted-foreground">
                        {category} · {item.timeframe} · {item.session}
                      </p>
                    </div>
                    <SignalBadge signal={item.signal} />
                  </div>

                  <div className="flex items-end justify-between gap-3">
                    <div>
                      <p className="font-mono text-lg tabular-nums text-primary">
                        {item.price
                          ? formatPrice(item.price, digits)
                          : "—"}
                      </p>
                      <p
                        className={cn(
                          "font-mono text-xs tabular-nums",
                          (item.changePercent ?? 0) >= 0
                            ? "text-bullish"
                            : "text-bearish",
                        )}
                      >
                        {(item.changePercent ?? 0) >= 0 ? "+" : ""}
                        {(item.changePercent ?? 0).toFixed(3)}%
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
                        Score
                      </p>
                      <p className="font-mono text-lg tabular-nums">
                        {formatPercent(item.confidence)}
                      </p>
                    </div>
                  </div>

                  <p className="text-xs text-muted">{item.reason}</p>
                  {inCrypto ? (
                    <Badge tone="warning">Crypto</Badge>
                  ) : null}
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
