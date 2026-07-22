import type { TradeEvaluation, TradeLearningRecord } from "../types";
import { clamp, round } from "../utils/math";

/** Score a closed trade across explainable accuracy dimensions. */
export function evaluateTrade(trade: TradeLearningRecord): TradeEvaluation {
  const notes: string[] = [];

  const predictionAccuracy =
    trade.predictionCorrect == null
      ? 50
      : trade.predictionCorrect
        ? 100
        : 0;
  if (trade.predictionCorrect === true) notes.push("Directional prediction matched outcome");
  if (trade.predictionCorrect === false) notes.push("Directional prediction missed");

  // Confidence vs outcome
  const conf = trade.confidenceAtEntry;
  let confidenceAccuracy = 50;
  if (trade.outcome === "win") {
    confidenceAccuracy = clamp(100 - Math.abs(conf - 75) * 0.4, 20, 100);
    if (conf >= 85 && trade.outcome === "win") notes.push("High confidence aligned with win");
  } else if (trade.outcome === "loss") {
    confidenceAccuracy = clamp(100 - conf * 0.7, 0, 80);
    if (conf >= 85) notes.push("High confidence preceded a loss — calibration risk");
  }

  const plannedRisk = Math.abs(trade.entry - trade.stopLoss) || 1;
  const riskAccuracy =
    trade.result === "sl"
      ? clamp(100 - trade.stopMoves * 15, 10, 90)
      : clamp(90 - trade.stopMoves * 12, 20, 100);
  if (trade.stopMoves > 0) {
    notes.push(`Stop moved ${trade.stopMoves} time(s)`);
  }

  const rewardAccuracy =
    trade.plannedRr <= 0
      ? 50
      : clamp(100 - Math.abs(trade.realizedRr - trade.plannedRr) * 25, 0, 100);

  // Timing: shorter holds on scalping wins score higher; losses held long score lower
  let timingAccuracy = 60;
  if (trade.outcome === "win" && trade.holdMinutes < (trade.strategy === "scalping" ? 30 : 240)) {
    timingAccuracy = 80;
  }
  if (trade.outcome === "loss" && trade.holdMinutes > 180) {
    timingAccuracy = 35;
    notes.push("Loss held relatively long");
  }
  if (trade.result === "tp1" || trade.result === "tp2" || trade.result === "tp3") {
    timingAccuracy = Math.max(timingAccuracy, 75);
  }

  const trendAccuracy =
    trade.supportingSignals.some((s) => /trend|bos|choch/i.test(s)) &&
    trade.outcome === "win"
      ? 85
      : trade.outcome === "loss" &&
          trade.opposingSignals.some((s) => /trend|bos|choch/i.test(s))
        ? 40
        : 60;

  const executionQuality = clamp(
    100 -
      trade.manualOverrides * 10 -
      trade.stopMoves * 8 -
      (trade.ignoredSignal ? 15 : 0),
    0,
    100,
  );

  const overallScore = round(
    predictionAccuracy * 0.15 +
      confidenceAccuracy * 0.15 +
      riskAccuracy * 0.15 +
      rewardAccuracy * 0.15 +
      timingAccuracy * 0.15 +
      trendAccuracy * 0.1 +
      executionQuality * 0.15,
    1,
  );

  void plannedRisk;

  return {
    tradeId: trade.id,
    predictionAccuracy,
    confidenceAccuracy: round(confidenceAccuracy, 1),
    riskAccuracy: round(riskAccuracy, 1),
    rewardAccuracy: round(rewardAccuracy, 1),
    timingAccuracy: round(timingAccuracy, 1),
    trendAccuracy: round(trendAccuracy, 1),
    executionQuality: round(executionQuality, 1),
    overallScore,
    notes,
  };
}
