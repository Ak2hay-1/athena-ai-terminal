import type {
  LearningStateBundle,
  TradeLearningRecord,
  LearningEvent,
  MarketMemoryEvent,
  PredictionRecord,
  MistakeEvent,
  ExplainableRecommendation,
  LearningGoal,
  Achievement,
  WeightVersion,
  TradeEvaluation,
  TraderProfile,
} from "../types";
import { DEFAULT_ACHIEVEMENTS as ACH_DEFS } from "../types";

const KEY_PREFIX = "athena.learning.user.";

function storageKey(userId: string): string {
  return `${KEY_PREFIX}${userId}.v1`;
}

export function emptyBundle(userId: string): LearningStateBundle {
  return {
    userId,
    events: [],
    trades: [],
    evaluations: [],
    predictions: [],
    mistakes: [],
    recommendations: [],
    goals: [],
    achievements: ACH_DEFS.map((a) => ({ ...a, progress: 0 })),
    marketMemory: [],
    weightHistory: [],
    profile: null,
    updatedAt: Date.now(),
  };
}

/** Per-user isolation — never mix histories. */
export function loadUserBundle(userId: string): LearningStateBundle {
  if (typeof window === "undefined" || !userId) return emptyBundle(userId || "anonymous");
  try {
    const raw = localStorage.getItem(storageKey(userId));
    if (raw) {
      const parsed = JSON.parse(raw) as LearningStateBundle;
      if (parsed.userId !== userId) return emptyBundle(userId);
      return {
        ...emptyBundle(userId),
        ...parsed,
        userId,
        achievements:
          parsed.achievements?.length
            ? parsed.achievements
            : emptyBundle(userId).achievements,
      };
    }
  } catch {
    /* ignore */
  }
  return emptyBundle(userId);
}

export function saveUserBundle(bundle: LearningStateBundle): void {
  if (typeof window === "undefined" || !bundle.userId) return;
  try {
    localStorage.setItem(
      storageKey(bundle.userId),
      JSON.stringify({ ...bundle, updatedAt: Date.now() }),
    );
  } catch {
    /* quota */
  }
}

export function exportUserBundle(userId: string): string {
  return JSON.stringify(loadUserBundle(userId), null, 2);
}

export function deleteUserLearningData(userId: string): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(storageKey(userId));
}

export function importUserBundle(json: string, expectedUserId: string): LearningStateBundle {
  const parsed = JSON.parse(json) as LearningStateBundle;
  if (parsed.userId && parsed.userId !== expectedUserId) {
    throw new Error("Import rejected: learning data belongs to another user.");
  }
  const bundle = { ...parsed, userId: expectedUserId, updatedAt: Date.now() };
  saveUserBundle(bundle);
  return bundle;
}
