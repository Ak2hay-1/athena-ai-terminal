import type { SignalSource, SignalWeights } from "../types";
import { DEFAULT_SIGNAL_WEIGHTS } from "../types";
import { clamp } from "../utils/math";

/** Resolve editable weight for a signal source. */
export function weightOf(
  source: SignalSource,
  weights: Partial<SignalWeights> = {},
): number {
  const merged = { ...DEFAULT_SIGNAL_WEIGHTS, ...weights };
  return Math.max(0, merged[source] ?? 0);
}

/** Normalize weighted scores so they are comparable across sources. */
export function applyWeight(
  strength: number,
  source: SignalSource,
  weights: Partial<SignalWeights>,
): number {
  const w = weightOf(source, weights);
  return clamp((strength / 100) * w, 0, w);
}

export function totalWeight(weights: Partial<SignalWeights> = {}): number {
  const merged = { ...DEFAULT_SIGNAL_WEIGHTS, ...weights };
  return Object.values(merged).reduce((s, v) => s + Math.max(0, v), 0) || 1;
}
