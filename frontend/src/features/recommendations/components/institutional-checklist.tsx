"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ChecklistItem } from "@/types";

const VALIDATION_FALLBACK: Array<{ key: string; name: string }> = [
  { key: "trend", name: "Higher Timeframe Trend" },
  { key: "bos", name: "BOS Confirmed" },
  { key: "choch", name: "CHOCH Confirmed" },
  { key: "liquidity", name: "Liquidity Sweep" },
  { key: "atr", name: "ATR Validation" },
  { key: "risk_reward", name: "Risk Reward" },
  { key: "news", name: "News Filter" },
];

export function InstitutionalChecklist({
  items,
  validation,
}: {
  items?: ChecklistItem[];
  validation?: Record<string, boolean>;
}) {
  const rows: ChecklistItem[] =
    items && items.length > 0
      ? items
      : validation
        ? VALIDATION_FALLBACK.map(({ key, name }) => ({
            name,
            passed: Boolean(validation[key]),
          }))
        : [];

  if (rows.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Institutional Checklist</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5">
        {rows.map((item) => (
          <div
            key={item.name}
            className="flex items-center gap-2 rounded-sm border border-border/60 bg-background/30 px-3 py-2 text-sm"
          >
            <span
              className={cn(
                "font-mono text-xs",
                item.passed ? "text-bullish" : "text-bearish",
              )}
            >
              {item.passed ? "✓" : "✗"}
            </span>
            <span className={item.passed ? "text-zinc-200" : "text-muted"}>
              {item.name}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
