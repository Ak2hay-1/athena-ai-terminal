"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SignalBadge } from "@/components/ui/signal-badge";
import { priceDigitsFor } from "@/constants/markets";
import { AiExplanationCard } from "@/features/ai/components/ai-explanation-card";
import { ConfidenceBreakdown } from "@/features/recommendations/components/confidence-breakdown";
import { HistoricalInsights } from "@/features/recommendations/components/historical-insights";
import { InstitutionalChecklist } from "@/features/recommendations/components/institutional-checklist";
import { MarketHeatmap } from "@/features/recommendations/components/market-heatmap";
import { SmartEntryZone } from "@/features/recommendations/components/smart-entry-zone";
import { TradeComparison } from "@/features/recommendations/components/trade-comparison";
import { TradeProbabilityCard } from "@/features/recommendations/components/trade-probability-card";
import { TradeQualityCard } from "@/features/recommendations/components/trade-quality-card";
import { relativeTime } from "@/lib/mappers";
import { formatPercent, formatPrice } from "@/lib/utils";
import { createJournalEntry } from "@/services/journal";
import {
  getRecommendationById,
  getRecommendationHistory,
} from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

export function RecommendationDetailView({ id }: { id: string }) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const symbol = useDashboardStore((s) => s.symbol);

  const historyQuery = useQuery({
    queryKey: ["recommendation", "history", symbol, 100],
    queryFn: () => getRecommendationHistory(symbol, null, 100),
    enabled: Boolean(user),
  });

  const byIdQuery = useQuery({
    queryKey: ["recommendation", "by-id", id],
    queryFn: () => getRecommendationById(id),
    enabled: Boolean(user),
  });

  const addToJournal = useMutation({
    mutationFn: async () => {
      const rec =
        byIdQuery.data ??
        historyQuery.data?.find((item) => item.id === id) ??
        historyQuery.data?.find((item) => String(item.id) === String(id));
      if (!rec) throw new Error("Recommendation not found");
      return createJournalEntry({
        entryType: "recommendation_review",
        title: `${rec.symbol} ${rec.signal} review`,
        body:
          rec.reasons.slice(0, 5).join(" · ") ||
          `${rec.trend} bias · ${formatPercent(rec.confidence)} confidence`,
        symbol: rec.symbol,
        recommendationId: Number(rec.id),
        tags: ["from_detail"],
      });
    },
    onSuccess: () => {
      router.push("/journal");
    },
  });

  const recommendation =
    byIdQuery.data ??
    historyQuery.data?.find((item) => item.id === id) ??
    historyQuery.data?.find((item) => String(item.id) === String(id));

  if (historyQuery.isLoading && byIdQuery.isLoading) {
    return (
      <div className="mx-auto max-w-[900px] py-16 text-center text-sm text-muted">
        Loading recommendation…
      </div>
    );
  }

  if (!recommendation) {
    return (
      <div className="mx-auto flex max-w-[900px] flex-col items-start gap-4 py-16">
        <p className="text-sm text-muted">Recommendation {id} not found in current history.</p>
        <Button asChild variant="secondary">
          <Link href="/history">Back to history</Link>
        </Button>
      </div>
    );
  }

  const digits = priceDigitsFor(recommendation.symbol, recommendation.entry);

  return (
    <div className="mx-auto max-w-[900px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Recommendation
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            {recommendation.symbol} · {recommendation.timeframe}
          </h1>
          <p className="mt-1 text-sm text-muted">
            {relativeTime(recommendation.createdAt)} · id {recommendation.id}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <SignalBadge signal={recommendation.signal} />
          <Badge tone="ai">{formatPercent(recommendation.confidence)}</Badge>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-5">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Entry</p>
            <p className="mt-1 font-mono text-xl">
              {formatPrice(recommendation.entry, digits)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Stop</p>
            <p className="mt-1 font-mono text-xl text-bearish">
              {formatPrice(recommendation.stopLoss, digits)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Target</p>
            <p className="mt-1 font-mono text-xl text-bullish">
              {formatPrice(recommendation.takeProfit, digits)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">RR</p>
            <p className="mt-1 font-mono text-xl">
              {recommendation.riskReward.toFixed(2)}x
            </p>
          </CardContent>
        </Card>
      </div>

      {recommendation.entryZone ? (
        <SmartEntryZone zone={recommendation.entryZone} digits={digits} />
      ) : null}

      {recommendation.confidenceBreakdown ? (
        <ConfidenceBreakdown data={recommendation.confidenceBreakdown} />
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Context</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Badge tone="primary">{recommendation.trend}</Badge>
          <Badge tone="warning">{recommendation.risk} risk</Badge>
          {recommendation.entryType ? (
            <Badge tone="default">{recommendation.entryType} entry</Badge>
          ) : null}
          {recommendation.confluence != null ? (
            <Badge tone="ai">Confluence {recommendation.confluence}</Badge>
          ) : null}
          {recommendation.slReason ? (
            <Badge tone="bearish">SL: {recommendation.slReason}</Badge>
          ) : null}
          {recommendation.tpReason ? (
            <Badge tone="bullish">TP: {recommendation.tpReason}</Badge>
          ) : null}
        </CardContent>
      </Card>

      <InstitutionalChecklist
        items={recommendation.checklist}
        validation={recommendation.validation}
      />

      <TradeProbabilityCard recommendation={recommendation} />
      <TradeQualityCard recommendation={recommendation} />
      <HistoricalInsights insights={recommendation.historicalInsights} />
      <TradeComparison recommendationId={recommendation.id} />

      <AiExplanationCard
        recommendationId={recommendation.id}
        symbol={recommendation.symbol}
        timeframe={recommendation.timeframe}
        fallbackReasons={recommendation.reasons}
      />

      {recommendation.heatmap ? <MarketHeatmap data={recommendation.heatmap} /> : null}

      <div className="flex flex-wrap gap-2">
        <Button asChild>
          <Link href={`/markets/${recommendation.symbol.toLowerCase()}`}>
            Open chart
          </Link>
        </Button>
        <Button asChild variant="secondary">
          <Link href="/history">All history</Link>
        </Button>
        <Button
          variant="ai"
          disabled={addToJournal.isPending}
          onClick={() => addToJournal.mutate()}
        >
          {addToJournal.isPending ? "Adding…" : "Add to journal review"}
        </Button>
      </div>
    </div>
  );
}
