import type { DetectionScore, TraceRef } from "../types";
import { uid } from "../../utils/uid";

export function scoreOf(partial: Partial<DetectionScore> & { confidence: number }): DetectionScore {
  const confidence = clamp(partial.confidence, 0, 100);
  const strength = clamp(partial.strength ?? confidence, 0, 100);
  const ageBars = partial.ageBars ?? 0;
  const retests = partial.retests ?? 0;
  const validity = clamp(partial.validity ?? 100 - ageBars * 0.5, 0, 100);
  const status = partial.status ?? "active";
  const score = clamp(
    confidence * 0.45 + strength * 0.3 + validity * 0.25 - retests * 2,
    0,
    100,
  );
  return { confidence, strength, ageBars, retests, validity, status, score };
}

export function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

export function makeId(prefix: string): string {
  return uid(prefix);
}

export function trace(ruleId: string, indices: number[], notes?: string): TraceRef {
  return { ruleId, candleIndices: indices, notes };
}

export function atrApprox(
  highs: number[],
  lows: number[],
  closes: number[],
  period = 14,
): number {
  if (closes.length < 2) return 0;
  const n = Math.min(period, closes.length - 1);
  let sum = 0;
  for (let i = closes.length - n; i < closes.length; i++) {
    const prev = closes[i - 1] ?? closes[i];
    sum += Math.max(
      highs[i] - lows[i],
      Math.abs(highs[i] - prev),
      Math.abs(lows[i] - prev),
    );
  }
  return sum / n;
}
