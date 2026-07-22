import type {
  AnalysisSnapshot,
  ConfluenceResult,
  IntelligenceSettings,
  TrendState,
} from "../../types";
import { clamp } from "../../utils/scoring";

/** Combine independent engines into bullish/bearish/neutral confluence. */
export function computeConfluence(
  snap: Omit<AnalysisSnapshot, "confluence" | "events" | "mtf" | "analyzedAt">,
  settings: IntelligenceSettings,
): ConfluenceResult {
  const drivers: ConfluenceResult["drivers"] = [];
  let bull = 0;
  let bear = 0;
  let neut = 0;

  const add = (
    source: string,
    weight: number,
    bias: "bullish" | "bearish" | "neutral",
  ) => {
    drivers.push({ source, weight, bias });
    if (bias === "bullish") bull += weight;
    else if (bias === "bearish") bear += weight;
    else neut += weight;
  };

  addTrend(snap.trend, add);

  const activeOb = snap.orderBlocks.filter((o) => o.status === "active");
  for (const ob of activeOb.slice(-3)) {
    add("order_block", ob.score * 0.15, ob.bias);
  }

  for (const f of snap.fvgs.filter((x) => x.status === "active").slice(-3)) {
    add("fvg", f.score * 0.12, f.bias);
  }

  for (const z of snap.zones.filter((z) => z.status === "active").slice(-3)) {
    add("supply_demand", z.score * 0.12, z.kind === "demand" ? "bullish" : "bearish");
  }

  for (const l of snap.levels.slice(0, 4)) {
    if (l.broken) continue;
    add("sr", l.score * 0.08, l.kind === "support" ? "bullish" : "bearish");
  }

  for (const liq of snap.liquidity.filter((l) => l.kind === "sweep").slice(-2)) {
    add("liquidity_sweep", liq.importance * 0.1, "neutral");
  }

  if (snap.volume.pressure === "buying") add("volume", snap.volume.score * 0.1, "bullish");
  if (snap.volume.pressure === "selling") add("volume", snap.volume.score * 0.1, "bearish");

  for (const p of snap.patterns.slice(-3)) {
    if (p.direction !== "neutral") add("pattern", p.confidence * 0.1, p.direction);
    else add("pattern", p.confidence * 0.05, "neutral");
  }

  const kill = snap.sessions.find((s) => s.killZone && s.active);
  if (kill) add("session_killzone", 8, "neutral");

  const total = bull + bear + neut || 1;
  const bullishScore = clamp((bull / total) * 100, 0, 100);
  const bearishScore = clamp((bear / total) * 100, 0, 100);
  const neutralScore = clamp((neut / total) * 100, 0, 100);
  const overallConfidence = clamp(
    Math.max(bullishScore, bearishScore) * (1 - Math.min(bullishScore, bearishScore) / 100),
    settings.confidenceThreshold * 0.5,
    99,
  );

  return {
    bullishScore,
    bearishScore,
    neutralScore,
    overallConfidence,
    drivers: drivers.sort((a, b) => b.weight - a.weight).slice(0, 12),
  };
}

function addTrend(
  trend: TrendState,
  add: (s: string, w: number, b: "bullish" | "bearish" | "neutral") => void,
) {
  const w = trend.confidence * 0.25;
  if (trend.direction === "bullish") add("trend", w, "bullish");
  else if (trend.direction === "bearish") add("trend", w, "bearish");
  else add("trend", w * 0.5, "neutral");
}
