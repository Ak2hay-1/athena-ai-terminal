"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LearningSymbolStat } from "@/services/learning";

export function SymbolPerformance({ items }: { items: LearningSymbolStat[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Symbol performance</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {items.length === 0 ? (
          <p className="text-sm text-muted">No symbol samples yet.</p>
        ) : (
          items.map((item) => (
            <div
              key={item.symbol}
              className="grid grid-cols-2 gap-2 rounded-sm border border-border/60 px-3 py-2 text-sm sm:grid-cols-6"
            >
              <p className="font-mono font-medium">{item.symbol}</p>
              <p className="text-muted">n={item.recommendations}</p>
              <p className="text-muted">WR {item.win_rate.toFixed(1)}%</p>
              <p className="text-muted">RR {item.avg_rr.toFixed(2)}</p>
              <p className="text-muted">Conf {item.avg_confidence.toFixed(0)}</p>
              <p className="text-muted">PF {item.profit_factor.toFixed(2)}</p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
