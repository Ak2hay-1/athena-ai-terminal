import type { AnalysisSnapshot } from "../../intelligence/types";
import type { MtfVote, MtfVotingResult } from "../types";
import { clamp } from "../utils/math";

function classToBias(
  c: string,
): "bullish" | "bearish" | "neutral" {
  if (c.includes("bull")) return "bullish";
  if (c.includes("bear")) return "bearish";
  return "neutral";
}

export function voteMultiTimeframe(analysis: AnalysisSnapshot): MtfVotingResult {
  const frames = analysis.mtf?.frames ?? [];
  const votes: MtfVote[] = frames.map((f) => ({
    timeframe: f.timeframe,
    bias: classToBias(f.classification),
    confidence: f.confidence,
  }));

  if (!votes.length) {
    const bias = analysis.trend.direction;
    return {
      votes: [
        {
          timeframe: analysis.timeframe,
          bias,
          confidence: analysis.trend.confidence,
        },
      ],
      alignmentScore: analysis.trend.confidence,
      conflictScore: 100 - analysis.trend.confidence,
      dominantBias: bias,
    };
  }

  let bull = 0;
  let bear = 0;
  let neut = 0;
  for (const v of votes) {
    const w = Math.max(10, v.confidence);
    if (v.bias === "bullish") bull += w;
    else if (v.bias === "bearish") bear += w;
    else neut += w;
  }
  const total = bull + bear + neut || 1;
  const dominantBias: MtfVotingResult["dominantBias"] =
    bull >= bear && bull >= neut
      ? "bullish"
      : bear >= bull && bear >= neut
        ? "bearish"
        : "neutral";

  const dominantShare =
    dominantBias === "bullish" ? bull : dominantBias === "bearish" ? bear : neut;
  const alignmentScore = clamp((dominantShare / total) * 100, 0, 100);
  const conflictScore = clamp(100 - alignmentScore, 0, 100);

  return {
    votes,
    alignmentScore: Math.round(alignmentScore),
    conflictScore: Math.round(conflictScore),
    dominantBias,
  };
}
