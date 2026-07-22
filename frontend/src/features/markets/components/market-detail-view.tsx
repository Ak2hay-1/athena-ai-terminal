"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MARKET_SYMBOLS, TIMEFRAMES, priceDigitsFor } from "@/constants/markets";
import { IndicatorHelp } from "@/features/ai/components/indicator-help";
import { BasicRangeChart } from "@/features/markets/components/chart/basic-range-chart";
import { toNumber } from "@/lib/mappers";
import { formatPrice } from "@/lib/utils";
import { getLatestCandle, getQuotes } from "@/services/market";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

export function MarketDetailView({ symbol }: { symbol: string }) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);
  const normalized = symbol.toUpperCase();
  const enabled = Boolean(user);

  useEffect(() => {
    setSymbol(normalized);
  }, [normalized, setSymbol]);

  const quoteQuery = useQuery({
    queryKey: ["market", "quotes", normalized, timeframe],
    queryFn: () => getQuotes([normalized], timeframe),
    enabled,
    refetchInterval: 1_000,
    staleTime: 500,
  });

  const latestQuery = useQuery({
    queryKey: ["market", "latest", normalized, timeframe],
    queryFn: () => getLatestCandle(normalized, timeframe),
    enabled,
    refetchInterval: 15_000,
  });

  const quote = quoteQuery.data?.[0];
  const lastPrice =
    quote?.mid ??
    (latestQuery.data ? toNumber(latestQuery.data.close) : 0);
  const digits = priceDigitsFor(normalized, lastPrice);
  const quotesLive = Boolean(quote?.mid);

  const chartHref = useMemo(
    () =>
      `/markets/${normalized.toLowerCase()}/chart?tf=${encodeURIComponent(timeframe)}`,
    [normalized, timeframe],
  );

  return (
    <div className="mx-auto max-w-[1400px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Markets
          </p>
          <div className="mt-1 flex flex-wrap items-baseline gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{normalized}</h1>
            <p className="font-mono text-xl tabular-nums text-primary">
              {lastPrice ? formatPrice(lastPrice, digits) : "—"}
            </p>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Badge tone={quotesLive ? "bullish" : "warning"}>
              {quotesLive ? "Live quotes" : "Waiting for quotes…"}
            </Badge>
            <span className="text-xs text-muted">
              {quote?.source === "tick" ? "Tick feed" : "Candle feed"} · {timeframe}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={normalized}
            onChange={(event) => {
              const next = event.target.value;
              setSymbol(next);
              router.push(`/markets/${next.toLowerCase()}`);
            }}
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
          <IndicatorHelp symbol={normalized} timeframe={timeframe} />
          <Link
            href={chartHref}
            className="inline-flex h-9 items-center rounded-sm border border-primary/40 bg-primary/10 px-3 text-sm text-primary hover:bg-primary/20"
          >
            Open Chart
          </Link>
          <Link
            href="/markets"
            className="inline-flex h-9 items-center rounded-sm border border-border px-3 text-sm text-muted hover:text-foreground"
          >
            All markets
          </Link>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{normalized} overview</CardTitle>
        </CardHeader>
        <CardContent>
          <BasicRangeChart
            symbol={normalized}
            chartTf={timeframe}
            enabled={enabled}
            height={300}
          />
        </CardContent>
      </Card>
    </div>
  );
}
