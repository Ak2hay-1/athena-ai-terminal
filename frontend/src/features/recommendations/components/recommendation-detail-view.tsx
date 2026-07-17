"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SignalBadge } from "@/components/ui/signal-badge";
import { priceDigitsFor } from "@/constants/markets";
import { relativeTime } from "@/lib/mappers";
import { formatPercent, formatPrice } from "@/lib/utils";
import { getRecommendationHistory } from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

export function RecommendationDetailView({ id }: { id: string }) {
  const user = useAuthStore((s) => s.user);
  const symbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);

  const historyQuery = useQuery({
    queryKey: ["recommendation", "history", symbol, timeframe, 100],
    queryFn: () => getRecommendationHistory(symbol, timeframe, 100),
    enabled: Boolean(user),
  });

  const recommendation =
    historyQuery.data?.find((item) => item.id === id) ??
    historyQuery.data?.find((item) => String(item.id) === String(id));

  if (historyQuery.isLoading) {
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

      <Card>
        <CardHeader>
          <CardTitle>Reasoning</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {recommendation.reasons.length === 0 ? (
            <p className="text-sm text-muted">No structured reasons stored for this signal.</p>
          ) : (
            recommendation.reasons.map((reason) => (
              <p
                key={reason}
                className="rounded-sm border border-border/60 bg-background/30 px-3 py-2 text-sm text-zinc-200"
              >
                {reason}
              </p>
            ))
          )}
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-2">
        <Button asChild>
          <Link href={`/markets/${recommendation.symbol.toLowerCase()}`}>
            Open chart
          </Link>
        </Button>
        <Button asChild variant="secondary">
          <Link href="/history">All history</Link>
        </Button>
        <Button asChild variant="ai">
          <Link href="/journal">Add to journal review</Link>
        </Button>
      </div>
    </div>
  );
}
