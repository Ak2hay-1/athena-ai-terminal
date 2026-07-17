import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SignalBadge } from "@/components/ui/signal-badge";
import { formatPercent } from "@/lib/utils";
import type { ScannerOpportunity } from "@/types";

export function ScannerPreview({ items }: { items: ScannerOpportunity[] }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Market Scanner</CardTitle>
        <Link href="/scanner" className="text-xs text-primary hover:underline">
          Open scanner
        </Link>
      </CardHeader>
      <CardContent className="grid gap-2 sm:grid-cols-3">
        {items.length === 0 ? (
          <p className="text-sm text-muted sm:col-span-3">
            No ranked opportunities yet — open the scanner for the full board.
          </p>
        ) : (
          items.slice(0, 3).map((item) => (
            <Link
              key={item.id}
              href={`/markets/${item.symbol.toLowerCase()}`}
              className="rounded-sm border border-border bg-background/40 p-3 transition-colors hover:border-primary/40"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="font-mono text-sm font-semibold tracking-wide">
                  {item.symbol}
                </p>
                <SignalBadge signal={item.signal} />
              </div>
              <p className="mt-2 text-[11px] uppercase tracking-wide text-muted">
                {item.timeframe} · {item.session}
              </p>
              <p className="mt-1 text-xs text-muted">{item.reason}</p>
              <p className="mt-2 font-mono text-sm tabular-nums text-primary">
                {formatPercent(item.confidence)}
              </p>
            </Link>
          ))
        )}
      </CardContent>
    </Card>
  );
}
