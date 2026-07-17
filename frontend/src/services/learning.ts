import { apiFetch } from "@/services/api-client";
import { toNumber } from "@/lib/mappers";
import type { LearningStats } from "@/types";

interface LearningStatsRaw {
  pattern_win_rates?: Record<string, number>;
  weights?: Record<string, number>;
  sample_size?: number;
  model_accuracy?: number | null;
}

export async function getLearningStats(
  symbol: string,
  timeframe: string,
): Promise<LearningStats> {
  const raw = await apiFetch<LearningStatsRaw>(
    `/learning/stats?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`,
  );

  return {
    patternWinRates: raw.pattern_win_rates ?? {},
    weights: raw.weights ?? {},
    sampleSize: Math.round(toNumber(raw.sample_size)),
    modelAccuracy:
      raw.model_accuracy == null ? null : toNumber(raw.model_accuracy),
  };
}
