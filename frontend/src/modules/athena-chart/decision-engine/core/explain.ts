import type {
  ConfidenceResult,
  ExplanationObject,
  NormalizedSignal,
  OpportunityBias,
  TradeGrade,
} from "../types";

export function buildExplanation(params: {
  bias: OpportunityBias;
  grade: TradeGrade;
  confidence: ConfidenceResult;
  supporting: NormalizedSignal[];
  opposing: NormalizedSignal[];
  rr: number;
}): ExplanationObject {
  const { bias, grade, confidence, supporting, opposing, rr } = params;
  const reasons = supporting.slice(0, 6).map((s) => s.label);
  const risks = opposing.slice(0, 4).map((s) => `Conflict: ${s.label}`);
  if (confidence.factors.volatility > 70) {
    risks.push("Elevated volatility (ATR)");
  }
  if (rr < 1.5) risks.push("Risk/reward below preferred threshold");

  const summary = `${bias.replace(/_/g, " ")} · grade ${grade} · confidence ${Math.round(confidence.score)}% (${confidence.label.replace(/_/g, " ")}) · RR ${rr.toFixed(2)}`;

  return {
    summary,
    reasons,
    risks,
    ruleIds: [
      ...supporting.map((s) => s.ruleId),
      ...opposing.map((s) => s.ruleId),
    ].slice(0, 20),
  };
}
