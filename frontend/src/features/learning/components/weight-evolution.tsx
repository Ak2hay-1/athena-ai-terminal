"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LearningWeightHistory } from "@/services/learning";

export function WeightEvolution({
  active,
  version,
  history,
}: {
  active: Record<string, number>;
  version: string;
  history: LearningWeightHistory[];
}) {
  const entries = Object.entries(active).sort((a, b) => b[1] - a[1]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Weight evolution</CardTitle>
        <p className="text-xs text-muted">Active version · {version}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {entries.map(([key, value]) => (
            <div
              key={key}
              className="rounded-sm border border-border/60 px-3 py-2 text-sm"
            >
              <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                {key}
              </p>
              <p className="mt-1 font-mono text-lg">{value.toFixed(2)}</p>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
            Recent versions
          </p>
          {history.length === 0 ? (
            <p className="text-sm text-muted">Baseline only — no updates yet.</p>
          ) : (
            history.slice(0, 8).map((row) => (
              <div
                key={row.version}
                className="rounded-sm border border-border/60 px-3 py-2 text-xs text-muted"
              >
                <span className="font-mono text-foreground">{row.version}</span>
                {row.is_active ? " · active" : ""}
                {row.reason ? ` · ${row.reason}` : ""}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
