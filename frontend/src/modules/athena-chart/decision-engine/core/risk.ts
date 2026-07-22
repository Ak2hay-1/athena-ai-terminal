import type { Candlestick } from "../../types";
import { computeAtr } from "../../engine/indicators/calculations";
import type {
  DecisionSettings,
  EntryPlan,
  RiskAssessment,
  RiskCategory,
} from "../types";
import { resolveProfile, riskModeMultiplier } from "../strategies/profiles";
import { clamp, lastFinite, roundPrice } from "../utils/math";

function categoryOf(score: number): RiskCategory {
  if (score >= 80) return "extreme";
  if (score >= 60) return "high";
  if (score >= 35) return "medium";
  return "low";
}

export function assessRisk(
  candles: Candlestick[],
  entry: EntryPlan,
  settings: DecisionSettings,
  confidenceScore: number,
  conflictScore: number,
): RiskAssessment {
  const profile = resolveProfile(settings);
  const mode = riskModeMultiplier(settings.riskMode);
  const price = candles[candles.length - 1]?.close ?? entry.entry;
  const atr = lastFinite(computeAtr(candles)) ?? entry.atrDistance;

  const riskPerUnit = Math.abs(entry.entry - entry.stopLoss) || atr;
  const dollarRisk =
    (settings.accountEquity * (settings.accountRiskPct / 100)) * mode.size;
  const positionSize =
    riskPerUnit > 0 ? roundPrice(dollarRisk / riskPerUnit, 4) : 0;

  const atrRisk = atr / (price || 1);
  const expectedDrawdown = clamp(atrRisk * 100 * 1.5 + conflictScore * 0.1, 0.2, 25);

  const leverageBase = clamp(1 / (atrRisk * 20 || 0.05), 1, 20);
  const recommendedLeverage = roundPrice(leverageBase * mode.leverage, 2);

  const riskScore =
    atrRisk * 400 +
    conflictScore * 0.35 +
    (100 - confidenceScore) * 0.25 +
    (entry.riskReward < 1.5 ? 15 : 0);

  return {
    maximumRisk: roundPrice(dollarRisk, 2),
    expectedDrawdown: Math.round(expectedDrawdown * 10) / 10,
    positionSize,
    atrRisk: Math.round(atrRisk * 10000) / 10000,
    recommendedLeverage,
    expectedHoldingBars: profile.holdingBarsHint,
    category: categoryOf(riskScore),
  };
}
