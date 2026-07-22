"use client";

import Link from "next/link";
import { useState } from "react";
import { priceDigitsFor } from "@/constants/markets";
import { AthenaChart } from "@/features/markets/components/athena-chart";
import { useRangeCandles } from "@/hooks/use-range-candles";
import {
  CHART_RANGES,
  DEFAULT_CHART_RANGE,
  type ChartRange,
} from "@/lib/chart-ranges";
import { cn, formatPrice } from "@/lib/utils";

interface Props {
  symbol: string;
  height?: number;
  className?: string;
  enabled?: boolean;
  chartTf?: string;
}

export function BasicRangeChart({
  symbol,
  height = 260,
  className,
  enabled = true,
  chartTf,
}: Props) {
  const [range, setRange] = useState<ChartRange>(DEFAULT_CHART_RANGE);
  const { candles, changePercent, isLoading, error } = useRangeCandles({
    symbol,
    range,
    enabled,
  });

  const last = candles.at(-1);
  const digits = priceDigitsFor(symbol, last?.close ?? 0);
  const up = changePercent >= 0;
  const chartHref = `/markets/${symbol.toLowerCase()}/chart${
    chartTf ? `?tf=${encodeURIComponent(chartTf)}` : ""
  }`;

  return (
    <div
      className={cn(
        "overflow-hidden rounded-sm border border-border bg-panel",
        className,
      )}
    >
      <div className="flex h-11 flex-wrap items-center justify-between gap-2 border-b border-border px-3">
        <div className="flex min-w-0 items-baseline gap-2">
          <span className="font-mono text-sm font-medium">{symbol.toUpperCase()}</span>
          {last ? (
            <span className="font-mono text-sm tabular-nums text-foreground">
              {formatPrice(last.close, digits)}
            </span>
          ) : null}
          <span
            className={cn(
              "font-mono text-[11px] tabular-nums",
              up ? "text-bullish" : "text-bearish",
            )}
          >
            {candles.length > 0
              ? `${up ? "+" : ""}${changePercent.toFixed(2)}%`
              : isLoading
                ? "…"
                : "—"}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-1">
          {CHART_RANGES.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setRange(item)}
              className={cn(
                "rounded-sm border px-1.5 py-0.5 text-[10px] uppercase tracking-wide transition-colors",
                range === item
                  ? "border-primary/40 bg-primary/10 text-primary"
                  : "border-border text-muted hover:text-foreground",
              )}
            >
              {item}
            </button>
          ))}
          <Link
            href={chartHref}
            className="ml-1 inline-flex h-7 items-center rounded-sm border border-primary/40 bg-primary/10 px-2.5 text-[11px] font-medium text-primary transition-colors hover:bg-primary/20"
          >
            Open Chart
          </Link>
        </div>
      </div>

      {candles.length > 0 ? (
        <AthenaChart
          candles={candles}
          height={height - 44}
          mode="overview"
          showToolbar={false}
          symbol={symbol}
          className="rounded-none border-0"
        />
      ) : (
        <div
          className="flex items-center justify-center text-xs text-muted"
          style={{ height: height - 44 }}
        >
          {isLoading
            ? "Loading…"
            : error
              ? error instanceof Error
                ? error.message
                : "Failed to load chart data"
              : `No data for ${range}`}
        </div>
      )}
    </div>
  );
}
