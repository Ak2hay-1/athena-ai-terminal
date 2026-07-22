"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SignalBadge } from "@/components/ui/signal-badge";
import { formatPercent, formatPrice, cn } from "@/lib/utils";
import { priceDigitsFor } from "@/constants/markets";
import type { ScannerOpportunity } from "@/types";

function ScannerCard({ item }: { item: ScannerOpportunity }) {
  const prevPrice = useRef(item.price);
  const [flash, setFlash] = useState<"up" | "down" | null>(null);
  const digits = priceDigitsFor(item.symbol, item.price ?? 0);
  const reason = item.reason || item.reasons?.slice(0, 2).join(" · ") || "";
  const score = item.score ?? item.confidence;

  useEffect(() => {
    if (item.price == null || prevPrice.current === item.price) return;
    const prev = prevPrice.current ?? item.price;
    setFlash(item.price > prev ? "up" : "down");
    prevPrice.current = item.price;
    const timer = window.setTimeout(() => setFlash(null), 450);
    return () => window.clearTimeout(timer);
  }, [item.price]);

  return (
    <Link
      href={`/markets/${item.symbol.toLowerCase()}`}
      className={cn(
        "rounded-sm border border-border bg-background/40 p-3 transition-colors hover:border-primary/40",
        flash === "up" && "flash-up",
        flash === "down" && "flash-down",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="font-mono text-sm font-semibold tracking-wide">
          {item.symbol}
        </p>
        <SignalBadge signal={item.signal} />
      </div>
      <p className="mt-2 text-[11px] uppercase tracking-wide text-muted">
        {item.timeframe} · {item.session}
        {item.marketWatchTag
          ? ` · ${item.marketWatchTag.replace(/_/g, " ")}`
          : ""}
      </p>
      {item.price != null ? (
        <p
          className={cn(
            "mt-1 font-mono text-xs tabular-nums",
            flash === "up" && "text-bullish",
            flash === "down" && "text-bearish",
            !flash && "text-primary",
          )}
        >
          {formatPrice(item.price, digits)}
        </p>
      ) : null}
      <p className="mt-1 line-clamp-2 text-xs text-muted">{reason}</p>
      <p className="mt-2 font-mono text-sm tabular-nums text-primary">
        {formatPercent(score)}
      </p>
    </Link>
  );
}

export function ScannerPreview({ items }: { items: ScannerOpportunity[] }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Market Scanner</CardTitle>
        <Link href="/scanner" className="text-xs text-primary hover:underline">
          Open scanner
        </Link>
      </CardHeader>
      <CardContent className="grid gap-2 sm:grid-cols-3">
        {items.length === 0 ? (
          <p className="text-sm text-muted sm:col-span-3">
            No ranked opportunities yet — open the scanner for the full board.
          </p>
        ) : (
          items.slice(0, 3).map((item) => (
            <ScannerCard key={item.id} item={item} />
          ))
        )}
      </CardContent>
    </Card>
  );
}
