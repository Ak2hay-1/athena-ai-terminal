import type { StructureEvent, SwingPoint, TrendClass, TrendState } from "../../types";
import { clamp } from "../../utils/scoring";

export function classifyTrend(
  swings: SwingPoint[],
  structure: StructureEvent[],
): TrendState {
  const recent = structure.filter((s) => s.scope === "external").slice(-8);
  let bull = 0;
  let bear = 0;
  for (const e of recent) {
    const w = e.label === "BOS" || e.label === "CHOCH" ? 2 : 1;
    if (e.direction === "bullish") bull += w;
    else bear += w;
  }

  const highs = swings.filter((s) => s.kind === "high").slice(-4);
  const lows = swings.filter((s) => s.kind === "low").slice(-4);
  let hh = 0;
  let ll = 0;
  for (let i = 1; i < highs.length; i++) if (highs[i].price > highs[i - 1].price) hh++;
  for (let i = 1; i < lows.length; i++) if (lows[i].price < lows[i - 1].price) ll++;

  const swingBias = hh - ll + (bull - bear);
  const mag = Math.abs(swingBias);
  let classification: TrendClass = "range";
  if (swingBias >= 4) classification = "strong_bullish";
  else if (swingBias >= 2) classification = "bullish";
  else if (swingBias >= 1) classification = "weak_bullish";
  else if (swingBias <= -4) classification = "strong_bearish";
  else if (swingBias <= -2) classification = "bearish";
  else if (swingBias <= -1) classification = "weak_bearish";

  const confidence = clamp(40 + mag * 12, 0, 95);
  const direction =
    classification.includes("bull")
      ? "bullish"
      : classification.includes("bear")
        ? "bearish"
        : "neutral";

  return { classification, confidence, direction, swingBias };
}
