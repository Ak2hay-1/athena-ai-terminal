import type { AnalysisSnapshot } from "../../intelligence/types";
import type {
  ConfidenceLabel,
  ConfidenceResult,
  NormalizedSignal,
} from "../types";
import { clamp } from "../utils/math";

function labelOf(score: number): ConfidenceLabel {
  if (score >= 85) return "very_high";
  if (score >= 70) return "high";
  if (score >= 55) return "moderate";
  if (score >= 40) return "low";
  return "very_low";
}

export function computeConfidence(
  signals: NormalizedSignal[],
  analysis: AnalysisSnapshot,
  dominant: "bullish" | "bearish" | "neutral",
): ConfidenceResult {
  const support = signals.filter((s) =>
    dominant === "neutral" ? s.bias === "neutral" : s.bias === dominant,
  );
  const oppose = signals.filter(
    (s) => s.bias !== "neutral" && s.bias !== dominant,
  );
  const supportW = support.reduce((s, x) => s + x.weightedScore, 0);
  const opposeW = oppose.reduce((s, x) => s + x.weightedScore, 0);
  const base = supportW + opposeW || 1;

  const trendAgreement = clamp(
    (signals.find((s) => s.source === "trend")?.strength ?? 40) *
      (signals.find((s) => s.source === "trend")?.bias === dominant ? 1 : 0.4),
    0,
    100,
  );

  const timeframeAgreement = analysis.mtf?.agreementPct ?? 50;

  const volSig = signals.find((s) => s.source === "volume");
  const volumeConfirmation =
    volSig && (volSig.bias === dominant || dominant === "neutral")
      ? volSig.strength
      : volSig
        ? volSig.strength * 0.35
        : 40;

  const liqConfirm = signals
    .filter((s) => s.source === "liquidity")
    .slice(0, 3)
    .reduce((s, x) => s + x.strength, 0);
  const liquidityConfirmation = clamp(liqConfirm / 3 || 35, 0, 100);

  const patternConfirmation = clamp(
    signals
      .filter((s) => s.source === "pattern" && s.bias === dominant)
      .reduce((s, x) => s + x.strength, 0) / 2 ||
      (dominant === "neutral" ? 45 : 30),
    0,
    100,
  );

  const momSources = signals.filter(
    (s) =>
      (s.source === "rsi" || s.source === "macd" || s.source === "vwap") &&
      (s.bias === dominant || dominant === "neutral"),
  );
  const momentumConfirmation = clamp(
    momSources.reduce((s, x) => s + x.strength, 0) / Math.max(1, momSources.length) || 40,
    0,
    100,
  );

  const atrSig = signals.find((s) => s.source === "atr");
  const volatility = atrSig?.strength ?? 40;

  const riskPenalty = opposeW / base * 100;
  const risk = clamp(100 - riskPenalty, 0, 100);

  const confluenceBoost = analysis.confluence.overallConfidence * 0.25;

  const score = clamp(
    trendAgreement * 0.18 +
      timeframeAgreement * 0.16 +
      volumeConfirmation * 0.12 +
      liquidityConfirmation * 0.1 +
      patternConfirmation * 0.1 +
      momentumConfirmation * 0.12 +
      (100 - Math.abs(volatility - 45)) * 0.06 +
      risk * 0.1 +
      confluenceBoost * 0.06 +
      (supportW / base) * 40,
    0,
    99,
  );

  return {
    score: Math.round(score * 10) / 10,
    label: labelOf(score),
    factors: {
      trendAgreement: Math.round(trendAgreement),
      timeframeAgreement: Math.round(timeframeAgreement),
      volumeConfirmation: Math.round(volumeConfirmation),
      liquidityConfirmation: Math.round(liquidityConfirmation),
      patternConfirmation: Math.round(patternConfirmation),
      momentumConfirmation: Math.round(momentumConfirmation),
      volatility: Math.round(volatility),
      risk: Math.round(risk),
    },
  };
}
