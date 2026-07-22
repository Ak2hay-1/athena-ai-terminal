import { apiFetch } from "@/services/api-client";
import { toNumber } from "@/lib/mappers";
import type { LearningStats } from "@/types";

interface LearningStatsRaw {
  pattern_win_rates?: Record<string, number>;
  weights?: Record<string, number>;
  sample_size?: number;
  model_accuracy?: number | null;
}

type Envelope<T> = {
  success?: boolean;
  data?: T;
};

export type LearningFeatureStat = {
  feature_key: string;
  win_rate: number;
  avg_rr: number;
  sample_size: number;
  profit_factor: number;
};

export type LearningSymbolStat = {
  symbol: string;
  recommendations: number;
  win_rate: number;
  avg_rr: number;
  avg_confidence: number;
  profit_factor: number;
};

export type LearningTimeframeStat = {
  timeframe: string;
  win_rate: number;
  avg_rr: number;
  trade_frequency: number;
  profit_factor: number;
  sample_size: number;
};

export type LearningRegimeStat = {
  regime: string;
  win_rate: number;
  avg_rr: number;
  sample_size: number;
  profit_factor: number;
};

export type LearningCalibrationBucket = {
  bucket: string;
  predicted_mid: number;
  actual_win_rate: number;
  sample_size: number;
};

export type LearningWeightHistory = {
  version: string;
  weights: Record<string, number>;
  learning_version: string;
  reason?: string | null;
  is_active: number;
  created_at?: string;
};

export type LearningDashboard = {
  sample_size: number;
  wins: number;
  losses: number;
  win_rate: number;
  profit_factor: number;
  weight_version: string;
  learning_version: string;
  features: LearningFeatureStat[];
  symbols: LearningSymbolStat[];
  timeframes: LearningTimeframeStat[];
  regimes: LearningRegimeStat[];
  strategies: Array<{
    combo_key: string;
    win_rate: number;
    avg_rr: number;
    sample_size: number;
    profit_factor: number;
  }>;
  calibration: LearningCalibrationBucket[];
  weights: Record<string, number>;
};

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

export async function getLearningDashboard(): Promise<LearningDashboard> {
  const response = await apiFetch<Envelope<LearningDashboard>>("/learning/dashboard");
  return (
    response.data ?? {
      sample_size: 0,
      wins: 0,
      losses: 0,
      win_rate: 0,
      profit_factor: 0,
      weight_version: "baseline",
      learning_version: "1.0.0",
      features: [],
      symbols: [],
      timeframes: [],
      regimes: [],
      strategies: [],
      calibration: [],
      weights: {},
    }
  );
}

export async function getLearningFeatures(): Promise<LearningFeatureStat[]> {
  const response = await apiFetch<Envelope<LearningFeatureStat[]>>("/learning/features");
  return response.data ?? [];
}

export async function getLearningSymbols(): Promise<LearningSymbolStat[]> {
  const response = await apiFetch<Envelope<LearningSymbolStat[]>>("/learning/symbols");
  return response.data ?? [];
}

export async function getLearningTimeframes(): Promise<LearningTimeframeStat[]> {
  const response = await apiFetch<Envelope<LearningTimeframeStat[]>>(
    "/learning/timeframes",
  );
  return response.data ?? [];
}

export async function getLearningRegimes(): Promise<LearningRegimeStat[]> {
  const response = await apiFetch<Envelope<LearningRegimeStat[]>>("/learning/regimes");
  return response.data ?? [];
}

export async function getLearningCalibration(): Promise<LearningCalibrationBucket[]> {
  const response = await apiFetch<Envelope<LearningCalibrationBucket[]>>(
    "/learning/calibration",
  );
  return response.data ?? [];
}

export async function getLearningWeights(symbol = "XAUUSD", timeframe = "M5") {
  const response = await apiFetch<
    Envelope<{
      active: Record<string, number>;
      version: string;
      history: LearningWeightHistory[];
    }>
  >(
    `/learning/weights?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`,
  );
  return (
    response.data ?? {
      active: {},
      version: "baseline",
      history: [],
    }
  );
}

export async function getLearningHistory() {
  const response = await apiFetch<
    Envelope<{
      learning_versions: Array<{ version: string; notes?: string; created_at?: string }>;
      weight_history: LearningWeightHistory[];
    }>
  >("/learning/history");
  return response.data ?? { learning_versions: [], weight_history: [] };
}
