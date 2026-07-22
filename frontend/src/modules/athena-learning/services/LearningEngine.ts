/**
 * Learning Engine — records everything, recomputes analytics incrementally.
 * Deterministic. No GPT. Per-user isolation.
 */

import type {
  AnalyticsSnapshot,
  LearningStateBundle,
  TradeLearningRecord,
  WeightVersion,
} from "../types";
import {
  emptyBundle,
  loadUserBundle,
  saveUserBundle,
  exportUserBundle,
  deleteUserLearningData,
  importUserBundle,
} from "../memory/persistence";
import { evaluateTrade } from "../evaluation/tradeEvaluation";
import { calibrateConfidence } from "../evaluation/calibration";
import { computeStrategyPerformance } from "../strategies/performance";
import { buildTraderProfile } from "../profiles/traderProfile";
import { detectBehaviors, buildMistakeEvents } from "../learning/behavior";
import { generateRecommendations } from "../recommendations/engine";
import { buildAnalyticsSnapshot } from "../analytics/snapshot";
import { ingestMarketMemory } from "../models/brain";
import { updateAchievements, updateGoals } from "../learning/goals";
import { appendEvent, evaluatePrediction, recordPrediction } from "../learning/predictions";
import {
  activateWeightVersion,
  newBaselineVersion,
  proposeWeightUpdate,
  rollbackToPrevious,
} from "../learning/adaptiveWeights";

export class LearningEngine {
  private bundle: LearningStateBundle;

  constructor(private userId: string) {
    this.bundle = loadUserBundle(userId);
    if (!this.bundle.weightHistory.length) {
      this.bundle.weightHistory = [newBaselineVersion()];
      this.persist();
    }
  }

  getState(): LearningStateBundle {
    return this.bundle;
  }

  /** Record a closed trade and refresh derived analytics. */
  recordTrade(trade: TradeLearningRecord): LearningStateBundle {
    if (trade.userId !== this.userId) {
      throw new Error("Privacy violation: trade userId mismatch");
    }
    // dedupe by id
    this.bundle.trades = [
      ...this.bundle.trades.filter((t) => t.id !== trade.id),
      trade,
    ].slice(-10_000);

    this.bundle.events = appendEvent(this.bundle.events, {
      at: Date.now(),
      userId: this.userId,
      type: "trade_closed",
      symbol: trade.symbol,
      timeframe: trade.timeframe,
      payload: {
        outcome: trade.outcome,
        confidence: trade.confidenceAtEntry,
        pnl: trade.pnl,
      },
    });

    const evaluation = evaluateTrade(trade);
    this.bundle.evaluations = [
      ...this.bundle.evaluations.filter((e) => e.tradeId !== trade.id),
      evaluation,
    ].slice(-10_000);

    // prediction linkage
    const pred = recordPrediction({
      at: trade.openedAt,
      symbol: trade.symbol,
      timeframe: trade.timeframe,
      bullishProbability: trade.probabilityBullish ?? 50,
      bearishProbability: trade.probabilityBearish ?? 50,
      confidence: trade.confidenceAtEntry,
    });
    this.bundle.predictions = [
      ...this.bundle.predictions,
      evaluatePrediction(pred, trade.outcome),
    ].slice(-10_000);

    this.bundle.marketMemory = [
      ...this.bundle.marketMemory,
      ingestMarketMemory(trade, []),
    ].slice(-50_000);

    this.recompute();
    this.persist();
    return this.bundle;
  }

  recompute(): void {
    const trades = this.bundle.trades;
    this.bundle.profile = buildTraderProfile(this.userId, trades);
    const behaviors = detectBehaviors(trades);
    this.bundle.mistakes = buildMistakeEvents(behaviors, trades).slice(-200);
    const strategies = computeStrategyPerformance(trades);
    const calibration = calibrateConfidence(trades);
    this.bundle.recommendations = generateRecommendations({
      profile: this.bundle.profile,
      strategies,
      behaviors,
      calibration,
    });

    const today = new Date().toISOString().slice(0, 10);
    const dailyCount = trades.filter(
      (t) => new Date(t.closedAt).toISOString().slice(0, 10) === today,
    ).length;

    this.bundle.goals = updateGoals(this.bundle.goals, trades, dailyCount);

    let noStopStreak = 0;
    for (const t of [...trades].reverse()) {
      if (t.stopMoves > 0) break;
      noStopStreak += 1;
    }
    this.bundle.achievements = updateAchievements(
      this.bundle.achievements,
      trades,
      7,
      noStopStreak,
    );

    // Propose weights (not auto-activate)
    const active =
      this.bundle.weightHistory.find((w) => w.active) ?? newBaselineVersion();
    const proposal = proposeWeightUpdate(active.weights, trades);
    if (
      proposal &&
      !this.bundle.weightHistory.some((w) => w.version === proposal.version)
    ) {
      this.bundle.weightHistory = [...this.bundle.weightHistory, proposal].slice(-50);
      this.bundle.events = appendEvent(this.bundle.events, {
        at: Date.now(),
        userId: this.userId,
        type: "weight_change",
        payload: { version: proposal.version, evidence: proposal.evidence },
      });
    }
  }

  getAnalytics(): AnalyticsSnapshot {
    return buildAnalyticsSnapshot(
      this.bundle.trades,
      this.bundle.evaluations,
      this.bundle.profile,
    );
  }

  activateWeights(version: string): WeightVersion[] {
    this.bundle.weightHistory = activateWeightVersion(
      this.bundle.weightHistory,
      version,
    );
    this.persist();
    return this.bundle.weightHistory;
  }

  rollbackWeights(): WeightVersion[] {
    this.bundle.weightHistory = rollbackToPrevious(this.bundle.weightHistory);
    this.persist();
    return this.bundle.weightHistory;
  }

  setGoals(goals: LearningStateBundle["goals"]): void {
    this.bundle.goals = goals;
    this.persist();
  }

  exportJson(): string {
    return exportUserBundle(this.userId);
  }

  wipe(): void {
    deleteUserLearningData(this.userId);
    this.bundle = emptyBundle(this.userId);
    this.bundle.weightHistory = [newBaselineVersion()];
    this.persist();
  }

  importJson(json: string): void {
    this.bundle = importUserBundle(json, this.userId);
  }

  private persist(): void {
    saveUserBundle(this.bundle);
  }
}

const engines = new Map<string, LearningEngine>();

export function getLearningEngine(userId: string): LearningEngine {
  const id = userId || "anonymous";
  let eng = engines.get(id);
  if (!eng) {
    eng = new LearningEngine(id);
    engines.set(id, eng);
  }
  return eng;
}

export function resetLearningEngineCache(): void {
  engines.clear();
}
