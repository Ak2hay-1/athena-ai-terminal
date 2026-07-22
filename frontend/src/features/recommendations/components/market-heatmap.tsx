"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { MarketHeatmap as MarketHeatmapData } from "@/types";

const ROWS: Array<{ key: keyof MarketHeatmapData; label: string }> = [
  { key: "trend", label: "Trend" },
  { key: "momentum", label: "Momentum" },
  { key: "structure", label: "Structure" },
  { key: "liquidity", label: "Liquidity" },
  { key: "volatility", label: "Volatility" },
  { key: "news", label: "News" },
  { key: "risk", label: "Risk" },
];

function toneClass(value: number): string {
  if (value >= 70) return "bg-bullish";
  if (value >= 40) return "bg-warning";
  return "bg-bearish";
}

export function MarketHeatmap({ data }: { data: MarketHeatmapData }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Market Heatmap</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {ROWS.map(({ key, label }) => {
          const value = data[key];
          return (
            <div key={key} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">{label}</span>
                <span className="font-mono text-zinc-200">{value}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-sm bg-background/60">
                <div
                  className={cn("h-full rounded-sm transition-all", toneClass(value))}
                  style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
                />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
