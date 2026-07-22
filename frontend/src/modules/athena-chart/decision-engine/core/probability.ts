import type { NormalizedSignal, ProbabilityModel } from "../types";
import { normalizeProbabilities } from "../utils/math";

export function computeProbabilities(
  signals: NormalizedSignal[],
  confluenceBull: number,
  confluenceBear: number,
  confluenceNeut: number,
): ProbabilityModel {
  let bull = 0;
  let bear = 0;
  let neut = 0;
  for (const s of signals) {
    if (s.bias === "bullish") bull += s.weightedScore;
    else if (s.bias === "bearish") bear += s.weightedScore;
    else neut += s.weightedScore * 0.6;
  }
  // Blend with confluence scores
  bull += confluenceBull * 0.35;
  bear += confluenceBear * 0.35;
  neut += confluenceNeut * 0.25;
  return normalizeProbabilities(bull, bear, neut);
}
