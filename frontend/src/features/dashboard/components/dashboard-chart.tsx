"use client";

import { BasicRangeChart } from "@/features/markets/components/chart/basic-range-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  symbol: string;
  timeframe?: string;
  enabled?: boolean;
}

export function DashboardChart({
  symbol,
  timeframe,
  enabled = true,
}: Props) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex-row items-center justify-between gap-3 space-y-0 py-3">
        <div>
          <CardTitle className="font-mono text-sm">{symbol}</CardTitle>
          <p className="mt-0.5 text-[11px] text-muted">
            Overview · open advanced chart for full tools
          </p>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <BasicRangeChart
          symbol={symbol}
          chartTf={timeframe}
          enabled={enabled}
          height={280}
          className="rounded-none border-0 border-t"
        />
      </CardContent>
    </Card>
  );
}
