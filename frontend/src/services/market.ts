import { apiFetch } from "@/services/api-client";
import type { Candle, MarketQuote } from "@/types";

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
): Promise<Candle[]> {
  try {
    return await apiFetch<Candle[]>(
      `/market/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`,
    );
  } catch {
    return [];
  }
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
