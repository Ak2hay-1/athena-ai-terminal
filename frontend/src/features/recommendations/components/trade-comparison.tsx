"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  compareRecommendations,
  getSimilarRecommendations,
} from "@/services/recommendations";

const ROW_KEYS: Array<{ key: string; label: string }> = [
  { key: "confidence", label: "Confidence" },
  { key: "probability", label: "Probability" },
  { key: "trend", label: "Trend" },
  { key: "liquidity", label: "Liquidity" },
  { key: "rr", label: "RR" },
  { key: "structure", label: "Structure" },
  { key: "quality", label: "Quality" },
  { key: "grade", label: "Grade" },
];

export function TradeComparison({ recommendationId }: { recommendationId: string }) {
  const [otherId, setOtherId] = useState("");
  const [activeOtherId, setActiveOtherId] = useState<string | null>(null);

  const similarQuery = useQuery({
    queryKey: ["recommendation", "similar", recommendationId],
    queryFn: () => getSimilarRecommendations(recommendationId, 8),
  });

  const comparisonQuery = useQuery({
    queryKey: ["recommendation", "comparison", recommendationId, activeOtherId],
    queryFn: () => compareRecommendations(recommendationId, activeOtherId!),
    enabled: Boolean(activeOtherId),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trade Comparison</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-end gap-2">
          <div className="min-w-[160px] flex-1">
            <label className="text-[11px] uppercase tracking-wide text-muted-foreground">
              Compare with recommendation id
            </label>
            <input
              className="mt-1 w-full rounded-sm border border-border bg-background px-3 py-2 font-mono text-sm"
              value={otherId}
              onChange={(e) => setOtherId(e.target.value)}
              placeholder="e.g. 42"
            />
          </div>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setActiveOtherId(otherId.trim() || null)}
            disabled={!otherId.trim()}
          >
            Compare
          </Button>
        </div>

        {similarQuery.data && similarQuery.data.length > 0 ? (
          <div className="space-y-1">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
              Similar trades
            </p>
            <div className="flex flex-wrap gap-2">
              {similarQuery.data.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className="rounded-sm border border-border/70 bg-background/30 px-2 py-1 font-mono text-xs hover:border-primary/40"
                  onClick={() => {
                    setOtherId(String(item.id));
                    setActiveOtherId(String(item.id));
                  }}
                >
                  #{item.id} · {(item.similarity * 100).toFixed(0)}%
                  {item.outcomeLabel ? ` · ${item.outcomeLabel}` : ""}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {comparisonQuery.isLoading ? (
          <p className="text-sm text-muted">Loading comparison…</p>
        ) : null}

        {comparisonQuery.data ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[420px] text-left text-sm">
              <thead>
                <tr className="border-b border-border text-[11px] uppercase tracking-wide text-muted-foreground">
                  <th className="py-2 pr-3 font-medium">Metric</th>
                  <th
                    className={cn(
                      "py-2 pr-3 font-medium",
                      comparisonQuery.data.winner === "A" && "text-bullish",
                    )}
                  >
                    A (current)
                  </th>
                  <th
                    className={cn(
                      "py-2 font-medium",
                      comparisonQuery.data.winner === "B" && "text-bullish",
                    )}
                  >
                    B (#{activeOtherId})
                  </th>
                </tr>
              </thead>
              <tbody>
                {ROW_KEYS.map(({ key, label }) => {
                  const row = comparisonQuery.data?.comparison[key];
                  if (!row) return null;
                  return (
                    <tr key={key} className="border-b border-border/50">
                      <td className="py-2 pr-3 text-muted-foreground">{label}</td>
                      <td
                        className={cn(
                          "py-2 pr-3 font-mono",
                          row.winner === "A" && "text-bullish",
                        )}
                      >
                        {formatCell(row.a)}
                      </td>
                      <td
                        className={cn(
                          "py-2 font-mono",
                          row.winner === "B" && "text-bullish",
                        )}
                      >
                        {formatCell(row.b)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="mt-3 text-xs text-muted-foreground">
              Overall winner:{" "}
              <span className="font-medium text-zinc-100">
                {comparisonQuery.data.winner}
              </span>
            </p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function formatCell(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return String(value);
}
