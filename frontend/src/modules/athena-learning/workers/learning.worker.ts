/// <reference lib="webworker" />
/**
 * Background analytics worker — incremental recompute without blocking UI.
 */
import { computeStrategyPerformance } from "../strategies/performance";
import { calibrateConfidence } from "../evaluation/calibration";
import { buildAnalyticsSnapshot } from "../analytics/snapshot";
import { buildTraderProfile } from "../profiles/traderProfile";
import type { TradeLearningRecord, TradeEvaluation } from "../types";

export type LearningWorkerRequest = {
  type: "recompute";
  id: string;
  userId: string;
  trades: TradeLearningRecord[];
  evaluations: TradeEvaluation[];
};

export type LearningWorkerResponse = {
  type: "recompute_result";
  id: string;
  analytics: ReturnType<typeof buildAnalyticsSnapshot>;
  strategies: ReturnType<typeof computeStrategyPerformance>;
  calibration: ReturnType<typeof calibrateConfidence>;
  profile: ReturnType<typeof buildTraderProfile>;
};

self.onmessage = (event: MessageEvent<LearningWorkerRequest>) => {
  const msg = event.data;
  if (msg.type === "recompute") {
    const profile = buildTraderProfile(msg.userId, msg.trades);
    const res: LearningWorkerResponse = {
      type: "recompute_result",
      id: msg.id,
      analytics: buildAnalyticsSnapshot(msg.trades, msg.evaluations, profile),
      strategies: computeStrategyPerformance(msg.trades),
      calibration: calibrateConfidence(msg.trades),
      profile,
    };
    self.postMessage(res);
  }
};

export {};
