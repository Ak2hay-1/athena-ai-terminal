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
import { RecentRecommendations } from "./recent-recommendations";
import { RecommendationHeroCard } from "./recommendation-hero-card";
import { ScannerPreview } from "./scanner-preview";
import { WatchlistTable } from "./watchlist-table";

export function DashboardView() {
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);
  const {
    enabled,
    symbol,
    timeframe,
    health,
    recommendation,
    timeframeSignals,
    recentRecommendations,
    newsContext,
    newsHeadlines,
    calendarEvents,
    newsRefreshing,
    newsDataUpdatedAt,
    watchlist,
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

  const marketLabel = marketStatus.marketOpen
    ? "active"
    : marketStatus.marketReason.toLowerCase().includes("weekend")
      ? "closed (weekend)"
      : "closed";

  return (
    <div className="mx-auto max-w-[1600px] space-y-4">
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="flex flex-wrap items-end justify-between gap-3 border-b border-border pb-3"
      >
        <div>
          <div className="flex flex-wrap items-center gap-1.5">
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
              Athena Terminal
            </p>
            <Badge tone={marketStatus.marketOpen ? "bullish" : "bearish"}>
              Market {marketStatus.marketOpen ? "Open" : "Closed"}
            </Badge>
            <Badge tone={marketStatus.feedConnected ? "primary" : "bearish"}>
              Feed {marketStatus.feedConnected ? "OK" : "Down"}
            </Badge>
            <Badge tone={wsConnected ? "bullish" : "warning"}>
              {wsConnected ? (
                <>
                  <Wifi className="mr-1 h-3 w-3" /> WS
                </>
              ) : (
                <>
                  <WifiOff className="mr-1 h-3 w-3" /> WS
                </>
              )}
            </Badge>
            <Badge tone="neutral">{marketStatus.session}</Badge>
          </div>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-balance">
            {greetingForHour()} — markets are{" "}
            <span className={marketStatus.marketOpen ? "text-bullish" : "text-bearish"}>
              {marketLabel}
            </span>
          </h2>
          <p className="mt-0.5 max-w-xl text-xs text-muted">
            {marketStatus.marketReason}
            {newsContext?.highImpactUpcoming
              ? " · High-impact news window approaching."
              : ""}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
            className="h-8 rounded-sm border border-border bg-panel px-2.5 font-mono text-xs outline-none focus:border-primary/50"
            aria-label="Symbol"
          >
            {MARKET_SYMBOLS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-1.5">
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
              Chart
            </span>
            <select
              value={timeframe}
              onChange={(event) => setTimeframe(event.target.value)}
              className="h-8 rounded-sm border border-border bg-panel px-2.5 font-mono text-xs outline-none focus:border-primary/50"
              aria-label="Chart timeframe"
              title="Chart candles only — trade suggestion uses the best overall setup"
            >
              {TIMEFRAMES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
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
        <div className="rounded-sm border border-bearish/30 bg-bearish/10 px-4 py-2.5 text-sm text-bearish">
          {error}
        </div>
      ) : null}

      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Market Status"
          value={marketStatus.marketOpen ? "Open" : "Closed"}
          hint={marketStatus.marketReason}
          tone={marketStatus.marketOpen ? "bullish" : "bearish"}
        />
        <MetricCard
          label="Current Session"
          value={marketStatus.session}
          hint="UTC session window"
          tone="primary"
        />
        <MetricCard
          label="Feed / API"
          value={health?.status === "healthy" ? "Healthy" : "Degraded"}
          hint={`DB ${health?.database ?? "n/a"}`}
          tone={health?.status === "healthy" ? "bullish" : "warning"}
        />
        <MetricCard
          label="Market Score"
          value={`${marketStatus.score}`}
          hint={`Vol ${marketStatus.volatility}`}
          tone="ai"
        />
      </div>

      {recommendation ? (
        <RecommendationHeroCard
          recommendation={recommendation}
          timeframeSignals={timeframeSignals}
        />
      ) : (
        <div className="rounded-sm border border-dashed border-border bg-panel/60 p-6 text-center">
          <p className="text-sm font-medium">No live recommendation yet</p>
          <p className="mt-1 text-sm text-muted">
            Run analysis for {symbol}, or wait for the scheduler to publish a setup.
            Chart timeframe does not filter the trade call.
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

      <div className="grid gap-3 xl:grid-cols-3">
        <div className="space-y-3 xl:col-span-2">
          <DashboardChart
            symbol={symbol}
            timeframe={timeframe}
            enabled={enabled}
          />
          <WatchlistTable items={watchlist} />
          <ScannerPreview items={scanner} />
        </div>
        <div className="space-y-3">
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
            dataUpdatedAt={newsDataUpdatedAt}
            symbol={symbol}
          />
          <RecentRecommendations items={recentRecommendations} />
          <ActivityTimeline events={activity} />
        </div>
      </div>
    </div>
  );
}
