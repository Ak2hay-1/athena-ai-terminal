import type {
  ConfidenceResult,
  MtfVotingResult,
  OpportunityBias,
  ProbabilityModel,
  TradeGrade,
} from "../types";
import { clamp } from "../utils/math";

export function classifyOpportunity(
  prob: ProbabilityModel,
  confidence: ConfidenceResult,
  mtf: MtfVotingResult,
  minConfidence: number,
): OpportunityBias {
  if (confidence.score < minConfidence * 0.7) return "neutral";

  const edge = prob.bullish - prob.bearish;
  const aligned =
    (edge > 0 && mtf.dominantBias === "bullish") ||
    (edge < 0 && mtf.dominantBias === "bearish");

  if (edge >= 35 && confidence.score >= 80 && aligned) return "strong_buy";
  if (edge >= 18 && confidence.score >= 62) return "buy";
  if (edge >= 8 && confidence.score >= 50) return "watch_buy";
  if (edge <= -35 && confidence.score >= 80 && aligned) return "strong_sell";
  if (edge <= -18 && confidence.score >= 62) return "sell";
  if (edge <= -8 && confidence.score >= 50) return "watch_sell";
  return "neutral";
}

export function directionOf(
  bias: OpportunityBias,
): "long" | "short" | "flat" {
  if (bias === "strong_buy" || bias === "buy" || bias === "watch_buy") return "long";
  if (bias === "strong_sell" || bias === "sell" || bias === "watch_sell")
    return "short";
  return "flat";
}

export function gradeTrade(params: {
  confidence: number;
  riskReward: number;
  mtfAlignment: number;
  supportCount: number;
  opposeCount: number;
  sessionActive: boolean;
  volatilityPenalty: number;
}): { grade: TradeGrade; qualityScore: number } {
  const {
    confidence,
    riskReward,
    mtfAlignment,
    supportCount,
    opposeCount,
    sessionActive,
    volatilityPenalty,
  } = params;

  let q =
    confidence * 0.35 +
    clamp(riskReward * 18, 0, 30) +
    mtfAlignment * 0.15 +
    clamp(supportCount * 4, 0, 20) -
    clamp(opposeCount * 5, 0, 25) -
    volatilityPenalty * 0.15;

  if (sessionActive) q += 4;
  q = clamp(q, 0, 100);

  let grade: TradeGrade = "Avoid";
  if (q >= 88 && riskReward >= 2) grade = "A+";
  else if (q >= 78 && riskReward >= 1.6) grade = "A";
  else if (q >= 68 && riskReward >= 1.4) grade = "B+";
  else if (q >= 58 && riskReward >= 1.2) grade = "B";
  else if (q >= 48) grade = "C";
  else grade = "Avoid";

  return { grade, qualityScore: Math.round(q * 10) / 10 };
}
