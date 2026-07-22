"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LearningFeatureStat } from "@/services/learning";

export function FeatureAnalytics({ items }: { items: LearningFeatureStat[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Feature performance</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {items.length === 0 ? (
          <p className="text-sm text-muted">No feature samples yet.</p>
        ) : (
          items.map((item) => (
            <div
              key={item.feature_key}
              className="grid grid-cols-2 gap-2 rounded-sm border border-border/60 px-3 py-2 text-sm sm:grid-cols-5"
            >
              <p className="font-medium sm:col-span-1">{item.feature_key}</p>
              <p className="text-muted">WR {item.win_rate.toFixed(1)}%</p>
              <p className="text-muted">RR {item.avg_rr.toFixed(2)}</p>
              <p className="text-muted">n={item.sample_size}</p>
              <p className="text-muted">PF {item.profit_factor.toFixed(2)}</p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
