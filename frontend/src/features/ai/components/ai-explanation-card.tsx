"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { explainTrade, type ExplanationSections } from "@/services/ai";
import { useAuthStore } from "@/store/auth-store";

const SECTION_LABELS: { key: keyof ExplanationSections; label: string }[] = [
  { key: "trend", label: "Trend" },
  { key: "momentum", label: "Momentum" },
  { key: "structure", label: "Structure" },
  { key: "liquidity", label: "Liquidity" },
  { key: "risk", label: "Risk" },
  { key: "entry_sl_tp", label: "Entry / SL / TP" },
  { key: "confidence", label: "Confidence" },
  { key: "probability", label: "Probability" },
  { key: "quality", label: "Quality" },
];

type Props = {
  recommendationId?: number | string;
  symbol?: string;
  timeframe?: string;
  fallbackReasons?: string[];
};

export function AiExplanationCard({
  recommendationId,
  symbol,
  timeframe,
  fallbackReasons = [],
}: Props) {
  const user = useAuthStore((s) => s.user);
  const [requested, setRequested] = useState(false);

  const query = useQuery({
    queryKey: ["ai", "explain-trade", recommendationId, symbol, timeframe],
    queryFn: () =>
      explainTrade({
        recommendationId,
        symbol,
        timeframe,
      }),
    enabled: Boolean(user && requested && (recommendationId || (symbol && timeframe))),
  });

  const reasons = query.data?.reasons?.length
    ? query.data.reasons
    : fallbackReasons;
  const sections = query.data?.sections;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3 space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-ai" />
            Athena reasoning
          </CardTitle>
          <p className="mt-1 text-xs text-muted">
            Explains the frozen recommendation — never invents a new trade.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {query.data?.cached ? <Badge tone="neutral">cached</Badge> : null}
          <Button
            variant="ai"
            size="sm"
            disabled={query.isFetching}
            onClick={() => {
              if (requested) {
                void query.refetch();
              } else {
                setRequested(true);
              }
            }}
          >
            {query.isFetching ? "Explaining…" : requested ? "Refresh" : "Explain"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {query.isError ? (
          <p className="text-sm text-bearish">
            {query.error instanceof Error
              ? query.error.message
              : "Explanation unavailable."}
          </p>
        ) : null}

        {sections ? (
          <div className="grid gap-2 sm:grid-cols-2">
            {SECTION_LABELS.map(({ key, label }) => {
              const text = sections[key]?.trim();
              if (!text) return null;
              return (
                <div
                  key={key}
                  className="rounded-sm border border-border/60 bg-background/30 px-3 py-2"
                >
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                    {label}
                  </p>
                  <p className="mt-1 text-sm text-zinc-200">{text}</p>
                </div>
              );
            })}
          </div>
        ) : null}

        {reasons.length === 0 && !sections ? (
          <p className="text-sm text-muted">
            {requested
              ? "No explanation returned yet."
              : "Stored reasons below — click Explain for a richer sectioned narrative."}
          </p>
        ) : (
          <div className="space-y-2">
            {reasons.map((reason, index) => (
              <p
                key={`${index}-${reason}`}
                className="rounded-sm border border-border/60 bg-background/30 px-3 py-2 text-sm text-zinc-200"
              >
                {reason}
              </p>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
