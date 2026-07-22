"use client";

import { useQuery } from "@tanstack/react-query";
import {
  DEFAULT_CHART_RANGE,
  rangeToCandleQuery,
  type ChartRange,
} from "@/lib/chart-ranges";
import { getCandles } from "@/services/market";
import type { Candle } from "@/types";

interface Options {
  symbol: string;
  range?: ChartRange;
  enabled?: boolean;
}

export function useRangeCandles({
  symbol,
  range = DEFAULT_CHART_RANGE,
  enabled = true,
}: Options) {
  const { timeframe, limit } = rangeToCandleQuery(range);
  const normalized = symbol.toUpperCase();

  const query = useQuery({
    queryKey: ["market", "range-candles", normalized, range, timeframe, limit],
    queryFn: () => getCandles(normalized, timeframe, limit),
    enabled: enabled && Boolean(normalized),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const candles: Candle[] = query.data ?? [];
  const first = candles[0];
  const last = candles[candles.length - 1];
  const changePercent =
    first && last && first.close > 0
      ? ((last.close - first.close) / first.close) * 100
      : 0;

  return {
    candles,
    timeframe,
    changePercent,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    error: query.error,
    refetch: query.refetch,
  };
}
