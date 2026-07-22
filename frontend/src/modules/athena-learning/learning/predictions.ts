import type {
  LearningEvent,
  PredictionRecord,
  TradeLearningRecord,
} from "../types";
import { uid } from "../utils/math";

export function recordPrediction(partial: Omit<PredictionRecord, "id">): PredictionRecord {
  return { ...partial, id: uid("pred") };
}

export function evaluatePrediction(
  pred: PredictionRecord,
  outcome: TradeLearningRecord["outcome"],
): PredictionRecord {
  const bullishCall = pred.bullishProbability >= pred.bearishProbability;
  const correct =
    outcome === "win"
      ? bullishCall || pred.bullishProbability > 55
      : outcome === "loss"
        ? !bullishCall || pred.bearishProbability > 55
        : undefined;
  // Simpler: if we predicted dominant bull and trade was long win, etc. — use outcome win/loss vs majority side
  const predictedSide = pred.bullishProbability >= pred.bearishProbability ? "bull" : "bear";
  let predictionCorrect: boolean | undefined;
  if (outcome === "win" || outcome === "loss") {
    // Without knowing trade direction on prediction alone, treat high-confidence majority as claim
    predictionCorrect =
      outcome === "win"
        ? pred.confidence >= 55
        : pred.confidence < 70;
    void predictedSide;
  }
  return {
    ...pred,
    actualOutcome: outcome,
    predictionCorrect: correct ?? predictionCorrect,
    evaluatedAt: Date.now(),
  };
}

export function appendEvent(
  events: LearningEvent[],
  event: Omit<LearningEvent, "id"> & { id?: string },
): LearningEvent[] {
  const full: LearningEvent = {
    id: event.id ?? uid("evt"),
    at: event.at,
    userId: event.userId,
    type: event.type,
    symbol: event.symbol,
    timeframe: event.timeframe,
    payload: event.payload,
  };
  return [...events, full].slice(-5000);
}
