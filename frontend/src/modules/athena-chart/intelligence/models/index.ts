/**
 * Domain models for Athena Intelligence.
 * Thin wrappers around scored detections — keep detectors pure;
 * models normalize IDs, status, and panel/timeline payloads.
 */

import type {
  AnalysisSnapshot,
  ConfluenceResult,
  FairValueGap,
  IntelligenceEvent,
  LiquidityPool,
  OrderBlock,
  PatternHit,
  PriceLevel,
  StructureEvent,
  TrendState,
  Zone,
} from "../types";

export interface TrendModel {
  label: string;
  classification: TrendState["classification"];
  confidence: number;
  direction: TrendState["direction"];
}

export interface StructureSummaryModel {
  latest: StructureEvent[];
  bosCount: number;
  chochCount: number;
  bias: "bullish" | "bearish" | "neutral";
}

export interface ConfluenceModel {
  bullish: number;
  bearish: number;
  neutral: number;
  confidence: number;
  drivers: string[];
}

export interface OpportunityModel {
  risk: string;
  opportunity: string;
  confluence: ConfluenceModel;
}

export function toTrendModel(trend: TrendState): TrendModel {
  return {
    label: trend.classification.replace(/_/g, " "),
    classification: trend.classification,
    confidence: trend.confidence,
    direction: trend.direction,
  };
}

export function toStructureSummary(events: StructureEvent[]): StructureSummaryModel {
  const latest = events.slice(-8);
  const bosCount = events.filter((e) => e.label === "BOS").length;
  const chochCount = events.filter((e) => e.label === "CHOCH").length;
  const bull = latest.filter((e) => e.direction === "bullish").length;
  const bear = latest.filter((e) => e.direction === "bearish").length;
  return {
    latest,
    bosCount,
    chochCount,
    bias: bull > bear + 1 ? "bullish" : bear > bull + 1 ? "bearish" : "neutral",
  };
}

export function toConfluenceModel(c: ConfluenceResult): ConfluenceModel {
  return {
    bullish: c.bullishScore,
    bearish: c.bearishScore,
    neutral: c.neutralScore,
    confidence: c.overallConfidence,
    drivers: c.drivers.map((d) => d.source),
  };
}

export function activeOrderBlocks(blocks: OrderBlock[], minScore = 40): OrderBlock[] {
  return blocks.filter((b) => b.status === "active" && b.score >= minScore);
}

export function openFvgs(fvgs: FairValueGap[], minScore = 40): FairValueGap[] {
  return fvgs.filter(
    (f) =>
      (f.status === "active" || f.status === "partial") && f.score >= minScore,
  );
}

export function freshZones(zones: Zone[], minScore = 40): Zone[] {
  return zones.filter((z) => !z.invalid && !z.mitigated && z.score >= minScore);
}

export function rankedLiquidity(pools: LiquidityPool[], limit = 8): LiquidityPool[] {
  return [...pools].sort((a, b) => b.score - a.score).slice(0, limit);
}

export function rankedPatterns(patterns: PatternHit[], limit = 5): PatternHit[] {
  return [...patterns].sort((a, b) => b.score - a.score).slice(0, limit);
}

export function rankedLevels(levels: PriceLevel[], limit = 10): PriceLevel[] {
  return [...levels].sort((a, b) => b.score - a.score).slice(0, limit);
}

export function toOpportunityModel(snap: AnalysisSnapshot): OpportunityModel {
  const c = toConfluenceModel(snap.confluence);
  const risk =
    c.confidence > 70
      ? "Elevated — high conviction setup"
      : c.confidence > 45
        ? "Moderate"
        : "Low conviction / choppy";
  const opportunity =
    c.bullish > c.bearish + 10
      ? `Bullish bias ${Math.round(c.bullish)}`
      : c.bearish > c.bullish + 10
        ? `Bearish bias ${Math.round(c.bearish)}`
        : "No clear directional edge";
  return { risk, opportunity, confluence: c };
}

export function timelineEvents(events: IntelligenceEvent[], limit = 24): IntelligenceEvent[] {
  return events.slice(-limit);
}
