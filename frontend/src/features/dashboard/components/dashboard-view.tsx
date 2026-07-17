"use client";

import { motion } from "framer-motion";
import { RefreshCw, Wifi, WifiOff } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { MARKET_SYMBOLS, TIMEFRAMES } from "@/constants/markets";
import { useDashboardData } from "@/hooks/use-dashboard-data";
import { formatPercent, greetingForHour } from "@/lib/utils";
import { useDashboardStore } from "@/store/dashboard-store";
import { ActivityTimeline } from "./activity-timeline";
import { DashboardChart } from "./dashboard-chart";
import { HighImpactNews } from "./high-impact-news";
import { OpenPositions } from "./open-positions";
import { RecentRecommendations } from "./recent-recommendations";
import { RecommendationHeroCard } from "./recommendation-hero-card";
import { ScannerPreview } from "./scanner-preview";
import { WatchlistTable } from "./watchlist-table";

export function DashboardView() {
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);
  const {
    symbol,
    timeframe,
    health,
    recommendation,
    recentRecommendations,
    newsContext,
    newsHeadlines,
    calendarEvents,
    newsRefreshing,
    positions,
    watchlist,
    candles,
    liveCandle,
    scanner,
    activity,
    marketStatus,
    wsConnected,
    isLoading,
    analyzing,
    analyze,
    refetchAll,
    error,
  } = useDashboardData();

  return (
    <div className="mx-auto max-w-[1400px] space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="flex flex-wrap items-end justify-between gap-4"
      >
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
              Athena Terminal
            </p>
            <Badge tone={wsConnected ? "bullish" : "warning"}>
              {wsConnected ? (
                <>
                  <Wifi className="mr-1 h-3 w-3" /> Live
                </>
              ) : (
                <>
                  <WifiOff className="mr-1 h-3 w-3" /> Live quotes
                </>
              )}
            </Badge>
            <Badge tone={health?.status === "healthy" ? "primary" : "bearish"}>
              API {health?.status ?? "unknown"}
            </Badge>
          </div>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight text-balance">
            {greetingForHour()} — markets are{" "}
            <span className={marketStatus.marketOpen ? "text-bullish" : "text-bearish"}>
              {marketStatus.marketOpen ? "active" : "degraded"}
            </span>
          </h2>
          <p className="mt-1 max-w-xl text-sm text-muted">
            Live recommendations, news context, and watchlist from Athena APIs.
            {newsContext?.highImpactUpcoming
              ? " High-impact news window approaching."
              : ""}
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
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void refetchAll()}
            disabled={isLoading}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            variant="ai"
            size="sm"
            onClick={() => void analyze()}
            disabled={analyzing}
          >
            {analyzing ? "Analyzing…" : "Run Analysis"}
          </Button>
        </div>
      </motion.div>

      {error ? (
        <div className="rounded-xl border border-bearish/30 bg-bearish/10 px-4 py-3 text-sm text-bearish">
          {error}
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Market Status"
          value={marketStatus.marketOpen ? "Open" : "Unhealthy"}
          hint={`DB ${health?.database ?? "n/a"}`}
          tone={marketStatus.marketOpen ? "bullish" : "bearish"}
        />
        <MetricCard
          label="Current Session"
          value={marketStatus.session}
          hint="UTC session window"
          tone="primary"
        />
        <MetricCard
          label="Volatility"
          value={marketStatus.volatility}
          hint="From confluence/confidence"
          tone={marketStatus.volatility === "High" ? "warning" : "default"}
        />
        <MetricCard
          label="Market Score"
          value={`${marketStatus.score}`}
          hint="Confluence composite"
          tone="ai"
        />
      </div>

      {recommendation ? (
        <RecommendationHeroCard recommendation={recommendation} />
      ) : (
        <div className="rounded-sm border border-dashed border-border bg-panel/60 p-8 text-center">
          <p className="text-sm font-medium">No live recommendation yet</p>
          <p className="mt-1 text-sm text-muted">
            Run analysis for {symbol} {timeframe}, or wait for the scheduler to publish one.
          </p>
          <Button
            className="mt-4"
            variant="ai"
            onClick={() => void analyze()}
            disabled={analyzing}
          >
            {analyzing ? "Analyzing…" : "Run Analysis"}
          </Button>
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <DashboardChart
            symbol={symbol}
            timeframe={timeframe}
            candles={candles}
            liveCandle={liveCandle}
          />
          <WatchlistTable items={watchlist} />
          <ScannerPreview items={scanner} />
        </div>
        <div className="space-y-4">
          <MetricCard
            label="AI Confidence"
            value={recommendation ? formatPercent(recommendation.confidence) : "—"}
            hint={recommendation ? `${recommendation.symbol} hero` : "Awaiting signal"}
            tone="ai"
            className="border-primary/20 bg-primary/5"
          />
          <HighImpactNews
            items={newsHeadlines}
            context={newsContext}
            calendar={calendarEvents}
            refreshing={newsRefreshing}
          />
          <OpenPositions positions={positions} />
          <RecentRecommendations items={recentRecommendations} />
          <ActivityTimeline events={activity} />
        </div>
      </div>
    </div>
  );
}
