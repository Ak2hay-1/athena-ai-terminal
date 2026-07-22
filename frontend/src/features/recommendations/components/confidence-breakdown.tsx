"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ConfidenceBreakdown as ConfidenceBreakdownData } from "@/types";

const ROWS: Array<{
  key: keyof Pick<
    ConfidenceBreakdownData,
    "trend" | "momentum" | "structure" | "liquidity" | "news" | "risk"
  >;
  maxKey: keyof Pick<
    ConfidenceBreakdownData,
    | "trendMax"
    | "momentumMax"
    | "structureMax"
    | "liquidityMax"
    | "newsMax"
    | "riskMax"
  >;
  label: string;
}> = [
  { key: "trend", maxKey: "trendMax", label: "Trend" },
  { key: "momentum", maxKey: "momentumMax", label: "Momentum" },
  { key: "structure", maxKey: "structureMax", label: "Structure" },
  { key: "liquidity", maxKey: "liquidityMax", label: "Liquidity" },
  { key: "news", maxKey: "newsMax", label: "News" },
  { key: "risk", maxKey: "riskMax", label: "Risk" },
];

export function ConfidenceBreakdown({
  data,
}: {
  data: ConfidenceBreakdownData;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Confidence Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {ROWS.map(({ key, maxKey, label }) => {
          const score = data[key];
          const max = Math.max(1, data[maxKey]);
          const pct = Math.min(100, (score / max) * 100);
          return (
            <div key={key} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">{label}</span>
                <span className="font-mono text-zinc-200">
                  {score}/{max}
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-sm bg-background/60">
                <div
                  className={cn(
                    "h-full rounded-sm transition-all",
                    pct >= 70
                      ? "bg-bullish"
                      : pct >= 40
                        ? "bg-warning"
                        : "bg-bearish",
                  )}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
