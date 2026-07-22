import { apiFetch } from "@/services/api-client";
import type { Candle, MarketQuote } from "@/types";

export interface MarketStatistics {
  symbol: string;
  timeframe: string;
  candle_count: number;
  first_candle: string | null;
  last_candle: string | null;
}

export interface MarketBackfillResult {
  symbol: string;
  timeframe: string;
  requested: number;
  inserted: number;
  candle_count: number;
  oldest: string | null;
  newest: string | null;
}

export async function getLatestCandle(
  symbol: string,
  timeframe: string,
): Promise<Candle | null> {
  try {
    return await apiFetch<Candle>(
      `/market/latest?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`,
    );
  } catch {
    return null;
  }
}

export async function getCandles(
  symbol: string,
  timeframe: string,
  limit = 50,
  options?: { before?: string },
): Promise<Candle[]> {
  const params = new URLSearchParams({
    symbol,
    timeframe,
    limit: String(limit),
  });
  if (options?.before) {
    params.set("before", options.before);
  }
  const url = `/market/candles?${params.toString()}`;
  return apiFetch<Candle[]>(url);
}

export async function getMarketStatistics(
  symbol: string,
  timeframe: string,
): Promise<MarketStatistics | null> {
  try {
    return await apiFetch<MarketStatistics>(
      `/market/statistics?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`,
    );
  } catch {
    return null;
  }
}

export async function backfillCandles(
  symbol: string,
  timeframe: string,
  count?: number,
): Promise<MarketBackfillResult> {
  return apiFetch<MarketBackfillResult>("/market/backfill", {
    method: "POST",
    body: JSON.stringify({
      symbol,
      timeframe,
      ...(count != null ? { count } : {}),
    }),
  });
}

export async function getQuotes(
  symbols: string[],
  timeframe = "M1",
): Promise<MarketQuote[]> {
  if (symbols.length === 0) return [];
  try {
    const query = symbols.map((s) => encodeURIComponent(s)).join(",");
    return await apiFetch<MarketQuote[]>(
      `/market/quotes?symbols=${query}&timeframe=${encodeURIComponent(timeframe)}`,
    );
  } catch {
    return [];
  }
}
