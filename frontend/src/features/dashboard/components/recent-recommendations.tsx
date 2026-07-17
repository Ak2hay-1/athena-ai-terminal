import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SignalBadge } from "@/components/ui/signal-badge";
import { formatPercent } from "@/lib/utils";
import type { Recommendation } from "@/types";

export function RecentRecommendations({
  items,
}: {
  items: Recommendation[];
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Recent Recommendations</CardTitle>
        <Link href="/history" className="text-xs text-primary hover:underline">
          History
        </Link>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? (
          <p className="text-sm text-muted">No recommendation history yet.</p>
        ) : (
          items.map((item) => (
            <Link
              key={item.id}
              href={`/recommendations/${item.id}`}
              className="flex items-center justify-between rounded-lg border border-border/70 bg-background/30 px-3 py-2.5 transition-colors hover:border-primary/30 hover:bg-primary/5"
            >
              <div>
                <p className="text-sm font-medium">
                  {item.symbol} · {item.timeframe}
                </p>
                <p className="text-xs text-muted">
                  RR {item.riskReward.toFixed(1)}x · {item.risk} risk
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs tabular-nums text-muted">
                  {formatPercent(item.confidence)}
                </span>
                <SignalBadge signal={item.signal} />
              </div>
            </Link>
          ))
        )}
      </CardContent>
    </Card>
  );
}
