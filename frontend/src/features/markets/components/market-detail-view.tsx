"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MARKET_SYMBOLS, TIMEFRAMES, priceDigitsFor } from "@/constants/markets";
import { PriceChart } from "@/features/markets/components/price-chart";
import { useMarketWebSocket } from "@/hooks/use-market-websocket";
import { toNumber } from "@/lib/mappers";
import { applyQuoteToCandle, formatPrice } from "@/lib/utils";
import { getCandles, getQuotes } from "@/services/market";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";
import type { Candle } from "@/types";

function mapCandle(
  raw: Record<string, unknown>,
  fallbacks: { symbol: string; timeframe: string },
): Candle | null {
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

export function MarketDetailView({ symbol }: { symbol: string }) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);
  const queryClient = useQueryClient();
  const normalized = symbol.toUpperCase();
  const enabled = Boolean(user);

  useEffect(() => {
    setSymbol(normalized);
  }, [normalized, setSymbol]);

  const candlesQuery = useQuery({
    queryKey: ["market", "candles", normalized, timeframe],
    queryFn: () => getCandles(normalized, timeframe, 300),
    enabled,
    refetchInterval: 30_000,
  });

  const quoteQuery = useQuery({
    queryKey: ["market", "quotes", normalized, timeframe],
    queryFn: () => getQuotes([normalized], timeframe),
    enabled,
    refetchInterval: 1_000,
    staleTime: 500,
  });

  const onWsMessage = useCallback(
    (payload: Record<string, unknown>) => {
      if (payload.type !== "candle_update") return;
      const updateSymbol = String(payload.symbol ?? "").toUpperCase();
      const updateTf = String(payload.timeframe ?? "").toUpperCase();
      if (updateSymbol !== normalized || updateTf !== timeframe.toUpperCase()) {
        return;
      }
      const candleRaw = payload.candle as Record<string, unknown> | undefined;
      const mapped = candleRaw
        ? mapCandle(candleRaw, { symbol: normalized, timeframe })
        : null;
      if (!mapped) return;

      queryClient.setQueryData<Candle[]>(
        ["market", "candles", normalized, timeframe],
        (current) => {
          if (!current || current.length === 0) return [mapped];
          const next = [...current];
          const last = next[next.length - 1];
          if (last && last.time === mapped.time) {
            next[next.length - 1] = mapped;
          } else {
            next.push(mapped);
            if (next.length > 400) next.shift();
          }
          return next;
        },
      );
    },
    [normalized, queryClient, timeframe],
  );

  const { connected } = useMarketWebSocket({
    symbols: [normalized],
    timeframe,
    onMessage: onWsMessage,
    enabled,
  });

  const candles = candlesQuery.data ?? [];
  const quote = quoteQuery.data?.[0];
  const lastCandle = candles.at(-1) ?? null;
  const liveCandle = useMemo(() => {
    if (!lastCandle) return null;
    if (quote?.mid) return applyQuoteToCandle(lastCandle, quote.mid);
    return lastCandle;
  }, [lastCandle, quote?.mid]);

  const lastPrice = quote?.mid ?? liveCandle?.close ?? 0;
  const digits = priceDigitsFor(normalized, lastPrice);
  const quotesLive = Boolean(quote?.mid);

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
            <Badge tone={connected ? "bullish" : quotesLive ? "warning" : "bearish"}>
              {connected
                ? "Live stream"
                : quotesLive
                  ? "Live quotes"
                  : "Stream reconnecting…"}
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
          <CardTitle>
            {normalized} · {timeframe}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {candles.length > 0 ? (
            <PriceChart candles={candles} liveCandle={liveCandle} height={420} />
          ) : (
            <div className="flex h-[420px] items-center justify-center rounded-sm border border-dashed border-border text-sm text-muted">
              {enabled
                ? `No candle data for ${normalized} ${timeframe}`
                : "Sign in to load live market charts"}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
