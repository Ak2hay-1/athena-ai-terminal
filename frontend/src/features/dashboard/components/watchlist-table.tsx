"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { SignalBadge } from "@/components/ui/signal-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { priceDigitsFor } from "@/constants/markets";
import { cn, formatPercent, formatPrice } from "@/lib/utils";
import type { WatchlistItem } from "@/types";

function WatchlistRow({ item }: { item: WatchlistItem }) {
  const prevPrice = useRef(item.price);
  const [flash, setFlash] = useState<"up" | "down" | null>(null);
  const digits = priceDigitsFor(item.symbol, item.price);

  useEffect(() => {
    if (prevPrice.current === item.price) return;
    setFlash(item.price > prevPrice.current ? "up" : "down");
    prevPrice.current = item.price;
    const timer = window.setTimeout(() => setFlash(null), 450);
    return () => window.clearTimeout(timer);
  }, [item.price]);

  return (
    <tr
      className={cn(
        "border-b border-border/60 last:border-0 transition-colors hover:bg-panel-elevated/50",
        flash === "up" && "flash-up",
        flash === "down" && "flash-down",
      )}
    >
      <td className="px-4 py-2.5 font-mono text-sm font-medium tracking-wide">
        <Link
          href={`/markets/${item.symbol.toLowerCase()}`}
          className="hover:text-primary"
        >
          {item.symbol}
        </Link>
      </td>
      <td
        className={cn(
          "px-3 py-2.5 font-mono text-sm tabular-nums",
          flash === "up" && "text-bullish",
          flash === "down" && "text-bearish",
        )}
      >
        {formatPrice(item.price, digits)}
      </td>
      <td className="px-3 py-2.5">
        <SignalBadge signal={item.signal} />
        {item.scannerGroup ? (
          <span className="mt-0.5 block text-[10px] uppercase tracking-wide text-muted-foreground">
            {item.scannerGroup.replace(/_/g, " ")}
            {item.setupQuality != null ? ` · Q${item.setupQuality}` : ""}
          </span>
        ) : null}
      </td>
      <td className="px-3 py-2.5 font-mono text-xs tabular-nums text-muted">
        {formatPercent(item.confidence)}
      </td>
      <td className="px-3 py-2.5 text-xs text-muted">{item.trend}</td>
      <td
        className={cn(
          "px-4 py-2.5 text-right font-mono text-xs tabular-nums",
          item.changePercent >= 0 ? "text-bullish" : "text-bearish",
        )}
      >
        {item.changePercent >= 0 ? "+" : ""}
        {item.changePercent.toFixed(3)}%
      </td>
    </tr>
  );
}

export function WatchlistTable({ items }: { items: WatchlistItem[] }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Watchlist</CardTitle>
        <Link href="/markets" className="text-xs text-primary hover:underline">
          View markets
        </Link>
      </CardHeader>
      <CardContent className="overflow-x-auto px-0">
        {items.length === 0 ? (
          <p className="px-4 text-sm text-muted">Loading live watchlist…</p>
        ) : (
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-y border-border bg-panel-elevated/40 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                <th className="px-4 py-2 font-medium">Symbol</th>
                <th className="px-3 py-2 font-medium">Last</th>
                <th className="px-3 py-2 font-medium">Signal</th>
                <th className="px-3 py-2 font-medium">Conf</th>
                <th className="px-3 py-2 font-medium">Trend</th>
                <th className="px-4 py-2 font-medium text-right">Chg%</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <WatchlistRow key={item.symbol} item={item} />
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  );
}
