"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  MARKET_CATEGORIES,
  MARKET_SYMBOLS,
  priceDigitsFor,
  symbolCategory,
} from "@/constants/markets";
import { cn, formatPrice } from "@/lib/utils";
import { getQuotes } from "@/services/market";
import {
  addWatchlistEntry,
  listWatchlist,
  removeWatchlistEntry,
  type WatchlistEntry,
} from "@/services/watchlist";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

function LivePrice({
  symbol,
  price,
  bid,
  ask,
  source,
  watched,
  onToggleWatch,
  busy,
}: {
  symbol: string;
  price: number;
  bid?: number;
  ask?: number;
  source?: string;
  watched: boolean;
  onToggleWatch: () => void;
  busy: boolean;
}) {
  const prev = useRef(price);
  const [flash, setFlash] = useState<"up" | "down" | null>(null);
  const digits = priceDigitsFor(symbol, price);

  useEffect(() => {
    if (!price || prev.current === price) return;
    setFlash(price > prev.current ? "up" : "down");
    prev.current = price;
    const timer = window.setTimeout(() => setFlash(null), 450);
    return () => window.clearTimeout(timer);
  }, [price]);

  return (
    <Card
      className={cn(
        "transition-colors hover:border-primary/40",
        flash === "up" && "flash-up",
        flash === "down" && "flash-down",
        watched && "border-ai/35",
      )}
    >
      <CardHeader className="flex-row items-center justify-between pb-2">
        <Link href={`/markets/${symbol.toLowerCase()}`}>
          <CardTitle className="font-mono tracking-wide hover:text-primary">
            {symbol}
          </CardTitle>
        </Link>
        <div className="flex items-center gap-1.5">
          <Badge tone="default">{symbolCategory(symbol)}</Badge>
          <Link
            href={`/markets/${symbol.toLowerCase()}/chart`}
            className="inline-flex h-7 items-center rounded-sm border border-primary/40 bg-primary/10 px-2 text-[10px] text-primary hover:bg-primary/20"
            onClick={(e) => e.stopPropagation()}
          >
            Chart
          </Link>
          <Button
            type="button"
            size="sm"
            variant={watched ? "ai" : "outline"}
            disabled={busy}
            onClick={onToggleWatch}
            className="h-7 px-2 text-[10px]"
          >
            {watched ? "Watching" : "Watch"}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Link href={`/markets/${symbol.toLowerCase()}`} className="block">
          <p
            className={cn(
              "font-mono text-xl tabular-nums",
              flash === "up" && "text-bullish",
              flash === "down" && "text-bearish",
            )}
          >
            {price ? formatPrice(price, digits) : "—"}
          </p>
          <div className="mt-2 flex gap-3 font-mono text-[11px] text-muted">
            <span>B {bid ? formatPrice(bid, digits) : "—"}</span>
            <span>A {ask ? formatPrice(ask, digits) : "—"}</span>
          </div>
          <p className="mt-2 text-[11px] uppercase tracking-wide text-muted-foreground">
            {source === "tick" ? "Live tick" : "Quote feed"}
          </p>
        </Link>
      </CardContent>
    </Card>
  );
}

export function MarketsListView() {
  const user = useAuthStore((s) => s.user);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const enabled = Boolean(user);
  const queryClient = useQueryClient();

  const quotesQuery = useQuery({
    queryKey: ["market", "quotes", "all", timeframe],
    queryFn: () => getQuotes([...MARKET_SYMBOLS], timeframe),
    enabled,
    refetchInterval: 1_000,
    staleTime: 500,
  });

  const watchlistQuery = useQuery({
    queryKey: ["watchlist", "entries"],
    queryFn: listWatchlist,
    enabled,
  });

  const watchedBySymbol = useMemo(() => {
    const map = new Map<string, WatchlistEntry>();
    for (const entry of watchlistQuery.data ?? []) {
      if (!entry.enabled) continue;
      map.set(entry.symbol.toUpperCase(), entry);
    }
    return map;
  }, [watchlistQuery.data]);

  const toggleMutation = useMutation({
    mutationFn: async (symbol: string) => {
      const existing = watchedBySymbol.get(symbol.toUpperCase());
      if (existing) {
        await removeWatchlistEntry(existing.id);
        return;
      }
      await addWatchlistEntry({ symbol, timeframe });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });

  const quoteMap = new Map(
    (quotesQuery.data ?? []).map((q) => [q.symbol.toUpperCase(), q]),
  );

  const sections = [
    { key: "metals", title: "Metals", symbols: MARKET_CATEGORIES.metals },
    { key: "forex", title: "FX Majors & Crosses", symbols: MARKET_CATEGORIES.forex },
  ] as const;

  return (
    <div className="mx-auto max-w-[1400px] space-y-6">
      <div className="border-b border-border pb-4">
        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
          Markets
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">Live board</h1>
        <p className="mt-1 text-sm text-muted">
          Quote board with personal watchlist · dashboard uses your watched symbols
        </p>
        {watchedBySymbol.size > 0 ? (
          <p className="mt-2 text-xs text-ai">
            Watching {watchedBySymbol.size} symbol
            {watchedBySymbol.size === 1 ? "" : "s"}
          </p>
        ) : (
          <p className="mt-2 text-xs text-muted">
            No personal watchlist yet — dashboard falls back to the full market list.
          </p>
        )}
      </div>

      {sections.map((section) => (
        <section key={section.key} className="space-y-3">
          <h2 className="text-[11px] font-medium uppercase tracking-[0.16em] text-primary">
            {section.title}
          </h2>
          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
            {section.symbols.map((symbol) => {
              const quote = quoteMap.get(symbol);
              return (
                <LivePrice
                  key={symbol}
                  symbol={symbol}
                  price={quote?.mid ?? 0}
                  bid={quote?.bid}
                  ask={quote?.ask}
                  source={quote?.source}
                  watched={watchedBySymbol.has(symbol)}
                  busy={toggleMutation.isPending}
                  onToggleWatch={() => toggleMutation.mutate(symbol)}
                />
              );
            })}
          </div>
        </section>
      ))}

      {!enabled ? (
        <p className="text-sm text-muted">Sign in to stream live market quotes.</p>
      ) : null}
    </div>
  );
}
