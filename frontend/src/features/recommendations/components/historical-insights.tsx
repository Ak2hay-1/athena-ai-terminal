"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function HistoricalInsights({ insights }: { insights?: string[] }) {
  if (!insights || insights.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Historical Insights</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5">
        {insights.map((insight) => (
          <div
            key={insight}
            className="flex items-start gap-2 rounded-sm border border-border/60 bg-background/30 px-3 py-2 text-sm text-zinc-200"
          >
            <span className="font-mono text-xs text-bullish">✓</span>
            <span>{insight}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
