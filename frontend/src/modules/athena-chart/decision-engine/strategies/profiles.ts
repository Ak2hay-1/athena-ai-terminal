import type {
  DecisionSettings,
  SignalWeights,
  StrategyProfileId,
} from "../types";
import { DEFAULT_SIGNAL_WEIGHTS } from "../types";

export interface StrategyProfile {
  id: StrategyProfileId;
  label: string;
  weights: SignalWeights;
  sensitivity: number;
  slAtrMult: number;
  tp1AtrMult: number;
  tp2AtrMult: number;
  tp3AtrMult: number;
  confidenceThreshold: number;
  minRiskReward: number;
  holdingBarsHint: number;
}

const base = (): SignalWeights => ({ ...DEFAULT_SIGNAL_WEIGHTS });

export const STRATEGY_PROFILES: Record<StrategyProfileId, StrategyProfile> = {
  scalping: {
    id: "scalping",
    label: "Scalping",
    weights: {
      ...base(),
      trend: 12,
      volume: 16,
      liquidity: 18,
      order_block: 14,
      fvg: 12,
      session: 14,
      rsi: 10,
      macd: 10,
      pattern: 6,
    },
    sensitivity: 0.75,
    slAtrMult: 0.8,
    tp1AtrMult: 1.0,
    tp2AtrMult: 1.6,
    tp3AtrMult: 2.4,
    confidenceThreshold: 60,
    minRiskReward: 1.2,
    holdingBarsHint: 12,
  },
  intraday: {
    id: "intraday",
    label: "Intraday",
    weights: { ...base() },
    sensitivity: 0.55,
    slAtrMult: 1.2,
    tp1AtrMult: 1.8,
    tp2AtrMult: 2.8,
    tp3AtrMult: 4.0,
    confidenceThreshold: 55,
    minRiskReward: 1.5,
    holdingBarsHint: 48,
  },
  swing: {
    id: "swing",
    label: "Swing",
    weights: {
      ...base(),
      trend: 24,
      swing_structure: 16,
      order_block: 16,
      pattern: 14,
      volume: 10,
      session: 4,
      rsi: 6,
      macd: 8,
    },
    sensitivity: 0.4,
    slAtrMult: 1.8,
    tp1AtrMult: 2.5,
    tp2AtrMult: 4.0,
    tp3AtrMult: 6.0,
    confidenceThreshold: 58,
    minRiskReward: 2.0,
    holdingBarsHint: 120,
  },
  position: {
    id: "position",
    label: "Position",
    weights: {
      ...base(),
      trend: 28,
      swing_structure: 18,
      support_resistance: 14,
      pattern: 12,
      volume: 8,
      session: 2,
      liquidity: 10,
      fvg: 8,
    },
    sensitivity: 0.3,
    slAtrMult: 2.5,
    tp1AtrMult: 3.5,
    tp2AtrMult: 5.5,
    tp3AtrMult: 8.0,
    confidenceThreshold: 62,
    minRiskReward: 2.5,
    holdingBarsHint: 240,
  },
};

export function resolveProfile(settings: DecisionSettings): StrategyProfile {
  const profile = STRATEGY_PROFILES[settings.strategy] ?? STRATEGY_PROFILES.intraday;
  return {
    ...profile,
    weights: { ...profile.weights, ...settings.signalWeights },
    confidenceThreshold: Math.max(
      profile.confidenceThreshold,
      settings.minConfidence,
    ),
    minRiskReward: Math.max(profile.minRiskReward, settings.minRiskReward),
  };
}

export function riskModeMultiplier(
  mode: DecisionSettings["riskMode"],
): { sl: number; size: number; leverage: number } {
  if (mode === "conservative") return { sl: 1.25, size: 0.7, leverage: 0.6 };
  if (mode === "aggressive") return { sl: 0.85, size: 1.3, leverage: 1.4 };
  return { sl: 1, size: 1, leverage: 1 };
}
