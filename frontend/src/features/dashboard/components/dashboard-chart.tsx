"use client";

import Link from "next/link";
import { PriceChart } from "@/features/markets/components/price-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Candle } from "@/types";

interface Props {
  symbol: string;
  timeframe: string;
  candles: Candle[];
  liveCandle: Candle | null;
}

export function DashboardChart({
  symbol,
  timeframe,
  candles,
  liveCandle,
}: Props) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-3">
        <div>
          <CardTitle>
            {symbol} · {timeframe}
          </CardTitle>
          <p className="mt-1 text-xs text-muted">Live candlestick chart</p>
        </div>
        <Link
          href={`/markets/${symbol.toLowerCase()}`}
          className="text-xs text-primary hover:underline"
        >
          Open market
        </Link>
      </CardHeader>
      <CardContent>
        {candles.length > 0 ? (
          <PriceChart candles={candles} liveCandle={liveCandle} height={320} />
        ) : (
          <div className="flex h-[320px] items-center justify-center rounded-xl border border-dashed border-border text-sm text-muted">
            No candle data yet for {symbol} {timeframe}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
