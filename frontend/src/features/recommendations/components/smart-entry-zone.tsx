"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatPrice } from "@/lib/utils";
import type { EntryZone } from "@/types";

export function SmartEntryZone({
  zone,
  digits,
}: {
  zone: EntryZone;
  digits: number;
}) {
  const optimal =
    zone.optimalLow === zone.optimalHigh
      ? formatPrice(zone.optimalLow, digits)
      : `${formatPrice(zone.optimalLow, digits)} – ${formatPrice(zone.optimalHigh, digits)}`;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Smart Entry Zone</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-sm border border-border/60 bg-background/30 px-3 py-3">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
            Aggressive
          </p>
          <p className="mt-1 font-mono text-lg text-zinc-100">
            {formatPrice(zone.aggressive, digits)}
          </p>
        </div>
        <div className="rounded-sm border border-primary/30 bg-primary/5 px-3 py-3">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
            Optimal
          </p>
          <p className="mt-1 font-mono text-lg text-zinc-100">{optimal}</p>
        </div>
        <div className="rounded-sm border border-border/60 bg-background/30 px-3 py-3">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
            Conservative
          </p>
          <p className="mt-1 font-mono text-lg text-zinc-100">
            {formatPrice(zone.conservative, digits)}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
