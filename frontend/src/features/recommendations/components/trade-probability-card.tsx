"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Recommendation } from "@/types";

export function TradeProbabilityCard({
  recommendation,
}: {
  recommendation: Recommendation;
}) {
  const detail = recommendation.probabilityDetail;
  const probability =
    detail?.probability ?? recommendation.tradeProbability ?? 0;
  const winRate =
    detail?.historicalWinRate ?? recommendation.historicalWinRate ?? 0;
  const similar =
    detail?.similarTrades ?? recommendation.similarTradeCount ?? 0;
  const expectedRr = detail?.expectedRr ?? recommendation.expectedRr ?? 0;
  const holdTime =
    detail?.expectedHoldTime ?? recommendation.expectedHoldTime ?? "—";
  const category = detail?.confidenceCategory;

  if (probability <= 0 && similar <= 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Win Probability</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1">
          <div className="flex items-end justify-between">
            <p className="font-mono text-3xl text-zinc-100">{probability}%</p>
            {category ? (
              <p
                className={cn(
                  "text-xs uppercase tracking-wide",
                  category === "LOW_SAMPLE" ? "text-warning" : "text-muted-foreground",
                )}
              >
                {category.replace(/_/g, " ")}
              </p>
            ) : null}
          </div>
          <div className="h-2 overflow-hidden rounded-sm bg-background/60">
            <div
              className={cn(
                "h-full rounded-sm",
                probability >= 75
                  ? "bg-bullish"
                  : probability >= 50
                    ? "bg-warning"
                    : "bg-bearish",
              )}
              style={{ width: `${Math.min(100, probability)}%` }}
            />
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <Stat label="Historical Win Rate" value={`${winRate}%`} />
          <Stat label="Similar Trades" value={String(similar)} />
          <Stat label="Expected RR" value={expectedRr.toFixed(2)} />
          <Stat label="Hold Time" value={holdTime || "—"} />
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-sm border border-border/60 bg-background/30 px-3 py-2">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 font-mono text-sm text-zinc-100">{value}</p>
    </div>
  );
}
