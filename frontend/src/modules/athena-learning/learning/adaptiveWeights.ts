import type { TradeLearningRecord, WeightVersion } from "../types";
import { uid } from "../utils/math";

const MIN_SAMPLES = 30;
const MIN_LIFT = 0.05;

/**
 * Controlled adaptive weights — requires statistical evidence.
 * Never silently mutates; returns a proposed version for review/activate.
 */
export function proposeWeightUpdate(
  current: Record<string, number>,
  trades: TradeLearningRecord[],
  reasonBase = "feature lift from personal outcomes",
): WeightVersion | null {
  const closed = trades.filter((t) => t.outcome === "win" || t.outcome === "loss");
  if (closed.length < MIN_SAMPLES) return null;

  const featureStats = new Map<string, { wins: number; n: number }>();
  for (const t of closed) {
    for (const s of t.supportingSignals) {
      const key = normalizeFeature(s);
      const cur = featureStats.get(key) ?? { wins: 0, n: 0 };
      cur.n += 1;
      if (t.outcome === "win") cur.wins += 1;
      featureStats.set(key, cur);
    }
  }

  const baseline = closed.filter((t) => t.outcome === "win").length / closed.length;
  const next = { ...current };
  const evidence: string[] = [];
  let changed = false;

  for (const [feature, st] of featureStats) {
    if (st.n < 10) continue;
    const wr = st.wins / st.n;
    const lift = wr - baseline;
    if (Math.abs(lift) < MIN_LIFT) continue;
    const weightKey = mapFeatureToWeight(feature);
    if (!weightKey || next[weightKey] == null) continue;
    const delta = lift > 0 ? 1 : -1;
    const proposed = Math.max(4, Math.min(28, next[weightKey] + delta));
    if (proposed !== next[weightKey]) {
      evidence.push(
        `${weightKey}: ${next[weightKey]}→${proposed} (feature ${feature} wr=${(wr * 100).toFixed(1)}% n=${st.n} lift=${(lift * 100).toFixed(1)}pts)`,
      );
      next[weightKey] = proposed;
      changed = true;
    }
  }

  if (!changed) return null;

  return {
    version: `w_${Date.now().toString(36)}`,
    weights: next,
    reason: reasonBase,
    evidence,
    sampleSize: closed.length,
    createdAt: Date.now(),
    active: false,
  };
}

export function activateWeightVersion(
  history: WeightVersion[],
  version: string,
): WeightVersion[] {
  return history.map((h) => ({
    ...h,
    active: h.version === version,
    rolledBack: h.active && h.version !== version ? true : h.rolledBack,
  }));
}

export function rollbackToPrevious(history: WeightVersion[]): WeightVersion[] {
  const sorted = [...history].sort((a, b) => b.createdAt - a.createdAt);
  const prev = sorted.find((h) => !h.active) ?? sorted[1];
  if (!prev) return history;
  return activateWeightVersion(history, prev.version);
}

function normalizeFeature(label: string): string {
  return label.toLowerCase().replace(/\s+/g, "_").slice(0, 48);
}

function mapFeatureToWeight(feature: string): string | null {
  if (feature.includes("liquidity") || feature.includes("sweep")) return "liquidity";
  if (feature.includes("trend") || feature.includes("bos")) return "trend";
  if (feature.includes("order_block") || feature.includes("ob")) return "order_block";
  if (feature.includes("fvg")) return "fvg";
  if (feature.includes("volume")) return "volume";
  if (feature.includes("pattern")) return "pattern";
  return null;
}

export function defaultWeights(): Record<string, number> {
  return {
    trend: 20,
    order_block: 18,
    liquidity: 16,
    fvg: 14,
    volume: 12,
    pattern: 10,
  };
}

export function newBaselineVersion(): WeightVersion {
  return {
    version: "baseline",
    weights: defaultWeights(),
    reason: "Initial baseline — no adaptation yet",
    evidence: ["factory defaults"],
    sampleSize: 0,
    createdAt: Date.now(),
    active: true,
  };
}

void uid;
