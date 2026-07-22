export type ChartRange = "1D" | "1W" | "1M" | "1Y" | "5Y";

export const CHART_RANGES: ChartRange[] = ["1D", "1W", "1M", "1Y", "5Y"];

export const DEFAULT_CHART_RANGE: ChartRange = "1M";

/** Map overview range → candle timeframe + fetch limit. */
export function rangeToCandleQuery(range: ChartRange): {
  timeframe: string;
  limit: number;
} {
  switch (range) {
    case "1D":
      return { timeframe: "M5", limit: 300 };
    case "1W":
      return { timeframe: "M15", limit: 700 };
    case "1M":
      return { timeframe: "H1", limit: 750 };
    case "1Y":
      return { timeframe: "D1", limit: 400 };
    case "5Y":
      return { timeframe: "D1", limit: 2000 };
  }
}
