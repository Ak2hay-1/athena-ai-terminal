import { create } from "zustand";
import type {
  Achievement,
  AnalyticsSnapshot,
  ExplainableRecommendation,
  LearningGoal,
  LearningStateBundle,
  MistakeEvent,
  TraderProfile,
  WeightVersion,
  StrategyPerformance,
  CalibrationBucket,
} from "../types";
import { getLearningEngine, resetLearningEngineCache } from "../services/LearningEngine";
import { calibrateConfidence } from "../evaluation/calibration";
import { computeStrategyPerformance } from "../strategies/performance";
import { createGoal } from "../learning/goals";
import { seedDemoTrades } from "../services/intake";

interface LearningStore {
  userId: string;
  bundle: LearningStateBundle | null;
  analytics: AnalyticsSnapshot | null;
  strategies: StrategyPerformance[];
  calibration: CalibrationBucket[];
  busy: boolean;
  setUserId: (userId: string) => void;
  refresh: () => void;
  ingestDemo: (n?: number) => void;
  addGoal: (
    title: string,
    metric: LearningGoal["metric"],
    target: number,
    unit: string,
  ) => void;
  activateWeights: (version: string) => void;
  rollbackWeights: () => void;
  exportData: () => string;
  deleteData: () => void;
  profile: () => TraderProfile | null;
  recommendations: () => ExplainableRecommendation[];
  mistakes: () => MistakeEvent[];
  achievements: () => Achievement[];
  weights: () => WeightVersion[];
}

export const useLearningStore = create<LearningStore>((set, get) => ({
  userId: "anonymous",
  bundle: null,
  analytics: null,
  strategies: [],
  calibration: [],
  busy: false,

  setUserId: (userId) => {
    resetLearningEngineCache();
    set({ userId });
    get().refresh();
  },

  refresh: () => {
    const eng = getLearningEngine(get().userId);
    eng.recompute();
    const bundle = eng.getState();
    set({
      bundle,
      analytics: eng.getAnalytics(),
      strategies: computeStrategyPerformance(bundle.trades),
      calibration: calibrateConfidence(bundle.trades),
    });
  },

  ingestDemo: (n = 48) => {
    const eng = getLearningEngine(get().userId);
    for (const t of seedDemoTrades(get().userId, n)) {
      eng.recordTrade(t);
    }
    get().refresh();
  },

  addGoal: (title, metric, target, unit) => {
    const eng = getLearningEngine(get().userId);
    const goals = [...eng.getState().goals, createGoal(title, metric, target, unit)];
    eng.setGoals(goals);
    get().refresh();
  },

  activateWeights: (version) => {
    getLearningEngine(get().userId).activateWeights(version);
    get().refresh();
  },

  rollbackWeights: () => {
    getLearningEngine(get().userId).rollbackWeights();
    get().refresh();
  },

  exportData: () => getLearningEngine(get().userId).exportJson(),

  deleteData: () => {
    getLearningEngine(get().userId).wipe();
    resetLearningEngineCache();
    get().refresh();
  },

  profile: () => get().bundle?.profile ?? null,
  recommendations: () => get().bundle?.recommendations ?? [],
  mistakes: () => get().bundle?.mistakes ?? [],
  achievements: () => get().bundle?.achievements ?? [],
  weights: () => get().bundle?.weightHistory ?? [],
}));
