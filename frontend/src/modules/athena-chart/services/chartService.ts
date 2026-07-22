import { getCandles } from "@/services/market";
import type { Candlestick } from "../types";
import { toApiTimeframe } from "../utils/timeframes";

/** React Query key factory. */
export const chartQueryKeys = {
  all: ["athena-chart"] as const,
  series: (symbol: string, timeframe: string) =>
    [...chartQueryKeys.all, "series", symbol, timeframe] as const,
};

export async function fetchChartSeries(params: {
  symbol: string;
  timeframe: string;
  count?: number;
}): Promise<Candlestick[]> {
  const apiTf = toApiTimeframe(params.timeframe);
  if (!apiTf) {
    throw new Error(
      `Timeframe ${params.timeframe} is not available for live data`,
    );
  }
  const batch = await getCandles(
    params.symbol.toUpperCase(),
    apiTf,
    params.count ?? 500,
  );
  return batch.map((c) => ({
    symbol: c.symbol,
    timeframe: c.timeframe,
    time: c.time,
    open: c.open,
    high: c.high,
    low: c.low,
    close: c.close,
    tick_volume: c.tick_volume,
  }));
}

export const chartService = {
  fetchSeries: fetchChartSeries,
  queryKeys: chartQueryKeys,
};
