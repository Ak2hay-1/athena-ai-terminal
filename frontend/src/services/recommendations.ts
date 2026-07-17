import { apiFetch } from "@/services/api-client";
import { mapRecommendation } from "@/lib/mappers";
import type { Recommendation } from "@/types";

export async function getLatestRecommendation(
  symbol: string,
  timeframe: string,
): Promise<Recommendation | null> {
  try {
    const raw = await apiFetch<Record<string, unknown> | null>(
      `/recommendations/latest?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`,
    );
    return mapRecommendation(raw ?? undefined, { symbol, timeframe });
  } catch {
    return null;
  }
}

export async function getRecommendationHistory(
  symbol: string,
  timeframe: string,
  limit = 20,
): Promise<Recommendation[]> {
  const raw = await apiFetch<Record<string, unknown>[]>(
    `/recommendations/history?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`,
  );
  return raw
    .map((item) => mapRecommendation(item, { symbol, timeframe }))
    .filter((item): item is Recommendation => item !== null);
}

export async function analyzeMarket(
  symbol: string,
  timeframe: string,
): Promise<{ success: boolean; recommendation?: Recommendation; message?: string }> {
  const result = await apiFetch<{
    success: boolean;
    message?: string;
    recommendation?: Record<string, unknown>;
  }>(`/ai/analyze?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`, {
    method: "POST",
  });

  return {
    success: result.success,
    message: result.message,
    recommendation: mapRecommendation(result.recommendation, { symbol, timeframe }) ?? undefined,
  };
}
