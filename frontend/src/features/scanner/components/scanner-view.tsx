"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { LayoutGrid, List, Wifi, WifiOff } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { SignalBadge } from "@/components/ui/signal-badge";
import {
  TIMEFRAMES,
  priceDigitsFor,
  symbolCategory,
} from "@/constants/markets";
import { useScannerData } from "@/hooks/use-scanner-data";
import { cn, formatPercent, formatPrice } from "@/lib/utils";
import type { ScannerOpportunity, Signal } from "@/types";

const SIGNAL_FILTERS: Array<"ALL" | Signal> = [
  "ALL",
  "STRONG_BUY",
  "BUY",
  "SELL",
  "STRONG_SELL",
  "HOLD",
  "NO_TRADE",
];

type SortMode = "score" | "change" | "freshness" | "rr";

function signalAccent(signal: Signal): string {
  if (signal.includes("BUY")) return "border-l-bullish bg-bullish/[0.04]";
  if (signal.includes("SELL")) return "border-l-bearish bg-bearish/[0.04]";
  if (signal === "NO_TRADE") return "border-l-warning bg-warning/[0.04]";
  return "border-l-border bg-transparent";
}

function ScoreBar({ value }: { value: number }) {
  const clamped = Math.max(0, Math.min(100, value));
  const tone =
    clamped >= 70 ? "bg-bullish" : clamped >= 50 ? "bg-primary" : "bg-zinc-500";
  return (
    <div className="flex min-w-[72px] items-center gap-2">
      <div className="h-1.5 flex-1 overflow-hidden rounded-sm bg-background/60">
        <div className={cn("h-full transition-all", tone)} style={{ width: `${clamped}%` }} />
      </div>
      <span className="w-8 text-right font-mono text-[11px] tabular-nums">
        {formatPercent(clamped)}
      </span>
    </div>
  );
}

function formatStale(ms?: number | null): string | null {
  if (ms == null || ms < 0) return null;
  const minutes = Math.round(ms / 60_000);
  if (minutes < 1) return "<1m";
  if (minutes < 60) return `${minutes}m`;
  return `${Math.round(minutes / 60)}h`;
}

function LevelsLine({ item }: { item: ScannerOpportunity }) {
  const digits = priceDigitsFor(item.symbol, item.entry ?? item.price ?? 0);
  if (!item.entry && !item.stopLoss && !item.takeProfit) return null;
  return (
    <p className="font-mono text-[10px] tabular-nums text-muted-foreground">
      {item.entry != null ? `E ${formatPrice(item.entry, digits)}` : null}
      {item.stopLoss != null ? ` · SL ${formatPrice(item.stopLoss, digits)}` : null}
      {item.takeProfit != null ? ` · TP ${formatPrice(item.takeProfit, digits)}` : null}
      {item.riskReward != null && item.riskReward > 0
        ? ` · R:R ${item.riskReward.toFixed(2)}`
        : null}
    </p>
  );
}

function usePriceFlash(price: number) {
  const prev = useRef(price);
  const [flash, setFlash] = useState<"up" | "down" | null>(null);

  useEffect(() => {
    if (!price || prev.current === price) return;
    setFlash(price > prev.current ? "up" : "down");
    prev.current = price;
    const timer = window.setTimeout(() => setFlash(null), 450);
    return () => window.clearTimeout(timer);
  }, [price]);

  return flash;
}

function ScannerTile({
  item,
  rank,
}: {
  item: ScannerOpportunity;
  rank: number;
}) {
  const price = item.price ?? 0;
  const changePercent = item.changePercent ?? 0;
  const flash = usePriceFlash(price);
  const digits = priceDigitsFor(item.symbol, price);
  const category = symbolCategory(item.symbol);
  const reason = item.reason || item.reasons.slice(0, 2).join(" · ");

  return (
    <Link href={`/markets/${item.symbol.toLowerCase()}`}>
      <Card
        className={cn(
          "h-full border-l-2 transition-colors hover:border-primary/40",
          signalAccent(item.signal),
          flash === "up" && "flash-up",
          flash === "down" && "flash-down",
          item.stale && "opacity-80",
        )}
      >
        <CardContent className="space-y-3 pt-5">
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] text-muted-foreground">#{rank}</span>
                <p className="font-mono text-base font-semibold tracking-wide">{item.symbol}</p>
                {item.marketWatchTag ? (
                  <Badge tone="warning" className="text-[9px] uppercase">
                    {item.marketWatchTag.replace(/_/g, " ")}
                  </Badge>
                ) : null}
              </div>
              <p className="mt-0.5 text-[11px] uppercase tracking-wide text-muted-foreground">
                {category} · {item.timeframe} · {item.session}
                {item.scannerGroup ? ` · ${item.scannerGroup.replace(/_/g, " ")}` : ""}
                {item.setupQuality != null ? ` · Q${item.setupQuality}` : ""}
                {item.alsoHotOn && item.alsoHotOn.length > 0
                  ? ` · also ${item.alsoHotOn.join("/")}`
                  : null}
              </p>
            </div>
            <SignalBadge signal={item.signal} />
          </div>

          <div className="flex items-end justify-between gap-3">
            <div>
              <p
                className={cn(
                  "font-mono text-lg tabular-nums",
                  flash === "up" && "text-bullish",
                  flash === "down" && "text-bearish",
                  !flash && "text-primary",
                )}
              >
                {price ? formatPrice(price, digits) : "—"}
              </p>
              <p
                className={cn(
                  "font-mono text-xs tabular-nums",
                  changePercent >= 0 ? "text-bullish" : "text-bearish",
                )}
              >
                {changePercent >= 0 ? "+" : ""}
                {changePercent.toFixed(3)}%
              </p>
            </div>
            <div className="w-28 space-y-1">
              <p className="text-right text-[10px] uppercase tracking-wide text-muted-foreground">
                Score
              </p>
              <ScoreBar value={item.score} />
              <p className="text-right font-mono text-[10px] text-muted-foreground">
                conf {formatPercent(item.confidence)}
              </p>
            </div>
          </div>

          <LevelsLine item={item} />
          <p className="line-clamp-2 text-xs text-muted">{reason || "—"}</p>
          {item.stale ? (
            <p className="text-[10px] uppercase tracking-wide text-warning">
              Stale · {formatStale(item.stalenessMs) ?? "outdated"}
            </p>
          ) : null}
        </CardContent>
      </Card>
    </Link>
  );
}

function BoardRow({ item, rank }: { item: ScannerOpportunity; rank: number }) {
  const price = item.price ?? 0;
  const changePercent = item.changePercent ?? 0;
  const flash = usePriceFlash(price);
  const digits = priceDigitsFor(item.symbol, price);
  const reason = item.reason || item.reasons.slice(0, 2).join(" · ");

  return (
    <tr
      className={cn(
        "border-b border-border/60 border-l-2 last:border-b-0 transition-colors hover:bg-panel-elevated/50",
        signalAccent(item.signal),
        flash === "up" && "flash-up",
        flash === "down" && "flash-down",
        item.stale && "opacity-80",
      )}
    >
      <td className="px-3 py-2.5 font-mono text-[11px] tabular-nums text-muted-foreground">
        {rank}
      </td>
      <td className="px-3 py-2.5">
        <Link
          href={`/markets/${item.symbol.toLowerCase()}`}
          className="font-mono text-sm font-semibold tracking-wide hover:text-primary"
        >
          {item.symbol}
        </Link>
        {item.marketWatchTag ? (
          <p className="mt-0.5 text-[10px] uppercase tracking-wide text-warning">
            {item.marketWatchTag.replace(/_/g, " ")}
          </p>
        ) : null}
        {item.alsoHotOn && item.alsoHotOn.length > 0 ? (
          <p className="mt-0.5 text-[10px] text-muted-foreground">
            also {item.alsoHotOn.join("/")}
          </p>
        ) : null}
      </td>
      <td className="px-3 py-2.5">
        <SignalBadge signal={item.signal} />
      </td>
      <td
        className={cn(
          "px-3 py-2.5 font-mono text-sm tabular-nums",
          flash === "up" && "text-bullish",
          flash === "down" && "text-bearish",
        )}
      >
        {price ? formatPrice(price, digits) : "—"}
      </td>
      <td
        className={cn(
          "px-3 py-2.5 font-mono text-xs tabular-nums",
          changePercent >= 0 ? "text-bullish" : "text-bearish",
        )}
      >
        {changePercent >= 0 ? "+" : ""}
        {changePercent.toFixed(3)}%
      </td>
      <td className="px-3 py-2.5">
        <ScoreBar value={item.score} />
        <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">
          conf {formatPercent(item.confidence)}
        </p>
      </td>
      <td className="px-3 py-2.5 font-mono text-[11px] tabular-nums text-muted">
        {item.riskReward != null && item.riskReward > 0
          ? item.riskReward.toFixed(2)
          : "—"}
        <LevelsLine item={item} />
      </td>
      <td className="max-w-[240px] px-3 py-2.5 text-xs text-muted">
        <span className="line-clamp-2">{reason || "—"}</span>
        {item.stale ? (
          <span className="mt-0.5 block text-[10px] uppercase text-warning">
            Stale {formatStale(item.stalenessMs)}
          </span>
        ) : null}
      </td>
      <td className="px-3 py-2.5 text-[11px] uppercase tracking-wide text-muted-foreground">
        {item.session}
      </td>
    </tr>
  );
}

export function ScannerView() {
  const {
    timeframe,
    setTimeframe,
    opportunities,
    meta,
    wsConnected,
    marketStatus,
    isLoading,
  } = useScannerData();

  const [signalFilter, setSignalFilter] = useState<(typeof SIGNAL_FILTERS)[number]>("ALL");
  const [categoryFilter, setCategoryFilter] = useState<"all" | "metals" | "forex">("all");
  const [minScore, setMinScore] = useState(0);
  const [actionableOnly, setActionableOnly] = useState(false);
  const [sortMode, setSortMode] = useState<SortMode>("score");
  const [viewMode, setViewMode] = useState<"board" | "tiles">("board");
  const [groupFilter, setGroupFilter] = useState<
    "all" | "elite" | "high_quality" | "watchlist" | "no_trade"
  >("all");

  const rows = useMemo(() => {
    const filtered = opportunities
      .filter((item) => (signalFilter === "ALL" ? true : item.signal === signalFilter))
      .filter((item) =>
        categoryFilter === "all"
          ? true
          : symbolCategory(item.symbol) === categoryFilter,
      )
      .filter((item) => item.score >= minScore)
      .filter((item) =>
        groupFilter === "all" ? true : item.scannerGroup === groupFilter,
      )
      .filter((item) =>
        actionableOnly
          ? item.signal !== "HOLD" &&
            item.signal !== "NEUTRAL" &&
            item.signal !== "NO_TRADE"
          : true,
      );

    const sorted = [...filtered];
    sorted.sort((a, b) => {
      const groupRank = (g?: string) =>
        ({ elite: 3, high_quality: 2, watchlist: 1, no_trade: 0 } as Record<
          string,
          number
        >)[g ?? ""] ?? 0;
      if (sortMode === "change") {
        return Math.abs(b.changePercent ?? 0) - Math.abs(a.changePercent ?? 0);
      }
      if (sortMode === "freshness") {
        const aMs = a.stalenessMs ?? Number.MAX_SAFE_INTEGER;
        const bMs = b.stalenessMs ?? Number.MAX_SAFE_INTEGER;
        return aMs - bMs;
      }
      if (sortMode === "rr") {
        return (b.riskReward ?? 0) - (a.riskReward ?? 0);
      }
      return (
        groupRank(b.scannerGroup) - groupRank(a.scannerGroup) ||
        b.score - a.score ||
        b.confidence - a.confidence
      );
    });
    return sorted;
  }, [
    actionableOnly,
    categoryFilter,
    groupFilter,
    minScore,
    opportunities,
    signalFilter,
    sortMode,
  ]);

  const metrics = useMemo(() => {
    const counts = meta?.groupCounts;
    const elite = counts?.elite ?? opportunities.filter((r) => r.scannerGroup === "elite").length;
    const highQuality =
      counts?.highQuality ??
      opportunities.filter((r) => r.scannerGroup === "high_quality").length;
    const watchlist =
      counts?.watchlist ??
      opportunities.filter((r) => r.scannerGroup === "watchlist").length;
    const noTrade =
      counts?.noTrade ??
      opportunities.filter((r) => r.scannerGroup === "no_trade").length;
    return { elite, highQuality, watchlist, noTrade, count: rows.length };
  }, [meta?.groupCounts, opportunities, rows.length]);

  const freshnessHint = useMemo(() => {
    if (!meta?.lastMarketWatchScanAgeMs && meta?.lastMarketWatchScanAgeMs !== 0) {
      return "Market Watch idle";
    }
    const age = formatStale(meta.lastMarketWatchScanAgeMs);
    return age ? `MW scan ${age} ago` : "MW scan live";
  }, [meta?.lastMarketWatchScanAgeMs]);

  return (
    <div className="mx-auto max-w-[1400px] space-y-4">
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4"
      >
        <div>
          <div className="flex flex-wrap items-center gap-1.5">
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
              Intelligence
            </p>
            <Badge tone={marketStatus.marketOpen ? "bullish" : "bearish"}>
              Market {marketStatus.marketOpen ? "Open" : "Closed"}
            </Badge>
            <Badge tone={wsConnected ? "bullish" : "warning"}>
              {wsConnected ? (
                <>
                  <Wifi className="mr-1 h-3 w-3" /> Live
                </>
              ) : (
                <>
                  <WifiOff className="mr-1 h-3 w-3" /> Quotes
                </>
              )}
            </Badge>
            <Badge tone="neutral">{marketStatus.session}</Badge>
            <Badge tone="neutral">{freshnessHint}</Badge>
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Market Scanner</h1>
          <p className="mt-1 text-sm text-muted">
            Server-ranked opportunities · {meta?.universeSize ?? "—"} symbols ·{" "}
            {timeframe}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-sm border border-border bg-panel p-0.5">
            <Button
              type="button"
              size="sm"
              variant={viewMode === "board" ? "default" : "ghost"}
              onClick={() => setViewMode("board")}
              className="h-8 gap-1.5"
            >
              <List className="h-3.5 w-3.5" />
              Board
            </Button>
            <Button
              type="button"
              size="sm"
              variant={viewMode === "tiles" ? "default" : "ghost"}
              onClick={() => setViewMode("tiles")}
              className="h-8 gap-1.5"
            >
              <LayoutGrid className="h-3.5 w-3.5" />
              Tiles
            </Button>
          </div>
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
      </motion.div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="★★★★★ Elite"
          value={`${metrics.elite}`}
          hint="Setup quality 90+"
          tone="bullish"
        />
        <MetricCard
          label="★★★★ High Quality"
          value={`${metrics.highQuality}`}
          hint="Setup quality 70–89"
          tone="primary"
        />
        <MetricCard
          label="★★★ Watchlist"
          value={`${metrics.watchlist}`}
          hint="Monitoring only"
          tone="warning"
        />
        <MetricCard
          label="No Trade"
          value={`${metrics.noTrade}`}
          hint="Rejected / stand aside"
          tone="ai"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {SIGNAL_FILTERS.map((signal) => (
            <Button
              key={signal}
              type="button"
              size="sm"
              variant={signalFilter === signal ? "default" : "outline"}
              onClick={() => setSignalFilter(signal)}
              className="h-8 text-[11px] uppercase tracking-wide"
            >
              {signal.replace("_", " ")}
            </Button>
          ))}
          <span className="mx-1 hidden h-8 w-px bg-border sm:inline-block" />
          {(["all", "metals", "forex"] as const).map((cat) => (
            <Button
              key={cat}
              type="button"
              size="sm"
              variant={categoryFilter === cat ? "secondary" : "outline"}
              onClick={() => setCategoryFilter(cat)}
              className="h-8 text-[11px] uppercase tracking-wide"
            >
              {cat}
            </Button>
          ))}
          <Button
            type="button"
            size="sm"
            variant={actionableOnly ? "default" : "outline"}
            onClick={() => setActionableOnly((v) => !v)}
            className="h-8 text-[11px] uppercase tracking-wide"
          >
            Actionable
          </Button>
          <span className="mx-1 hidden h-8 w-px bg-border sm:inline-block" />
          {(
            [
              ["all", "All desks"],
              ["elite", "Elite"],
              ["high_quality", "High Quality"],
              ["watchlist", "Watchlist"],
              ["no_trade", "No Trade"],
            ] as const
          ).map(([key, label]) => (
            <Button
              key={key}
              type="button"
              size="sm"
              variant={groupFilter === key ? "secondary" : "outline"}
              onClick={() => setGroupFilter(key)}
              className="h-8 text-[11px] uppercase tracking-wide"
            >
              {label}
            </Button>
          ))}
          <select
            value={sortMode}
            onChange={(event) => setSortMode(event.target.value as SortMode)}
            className="h-8 rounded-sm border border-border bg-panel px-2 font-mono text-[11px] outline-none"
          >
            <option value="score">Sort: score</option>
            <option value="change">Sort: change %</option>
            <option value="freshness">Sort: freshness</option>
            <option value="rr">Sort: R:R</option>
          </select>
          <label className="ml-auto flex items-center gap-2 text-xs text-muted">
            Min score
            <input
              type="range"
              min={0}
              max={90}
              step={5}
              value={minScore}
              onChange={(event) => setMinScore(Number(event.target.value))}
              className="accent-primary"
            />
            <span className="font-mono text-foreground">{minScore}</span>
          </label>
        </CardContent>
      </Card>

      {viewMode === "board" ? (
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Scanner board</CardTitle>
            <Badge tone="primary">{metrics.count} ranked</Badge>
          </CardHeader>
          <CardContent className="overflow-x-auto px-0">
            {isLoading && rows.length === 0 ? (
              <div className="space-y-2 px-4 py-4">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-10 animate-pulse rounded-sm bg-panel-elevated/80"
                  />
                ))}
              </div>
            ) : null}
            {!isLoading && rows.length === 0 ? (
              <p className="px-4 py-10 text-center text-sm text-muted">
                No opportunities match the current filters.
              </p>
            ) : null}
            {rows.length > 0 ? (
              <table className="w-full min-w-[980px] text-left">
                <thead>
                  <tr className="border-b border-border text-[10px] uppercase tracking-wide text-muted-foreground">
                    <th className="px-3 py-2 font-medium">#</th>
                    <th className="px-3 py-2 font-medium">Symbol</th>
                    <th className="px-3 py-2 font-medium">Signal</th>
                    <th className="px-3 py-2 font-medium">Price</th>
                    <th className="px-3 py-2 font-medium">Change</th>
                    <th className="px-3 py-2 font-medium">Score</th>
                    <th className="px-3 py-2 font-medium">Levels</th>
                    <th className="px-3 py-2 font-medium">Why now</th>
                    <th className="px-3 py-2 font-medium">Session</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((item, index) => (
                    <BoardRow key={item.id} item={item} rank={index + 1} />
                  ))}
                </tbody>
              </table>
            ) : null}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {isLoading && rows.length === 0
            ? Array.from({ length: 6 }).map((_, i) => (
                <Card key={i}>
                  <CardContent className="space-y-3 pt-5">
                    <div className="h-5 w-24 animate-pulse rounded-sm bg-panel-elevated" />
                    <div className="h-8 w-32 animate-pulse rounded-sm bg-panel-elevated" />
                    <div className="h-3 w-full animate-pulse rounded-sm bg-panel-elevated" />
                  </CardContent>
                </Card>
              ))
            : null}
          {!isLoading && rows.length === 0 ? (
            <Card className="sm:col-span-2 xl:col-span-3">
              <CardContent className="py-10 text-center text-sm text-muted">
                No opportunities match the current filters.
              </CardContent>
            </Card>
          ) : null}
          {rows.map((item, index) => (
            <ScannerTile key={item.id} item={item} rank={index + 1} />
          ))}
        </div>
      )}
    </div>
  );
}
