import type { AnalysisSnapshot } from "../../intelligence/types";
import type { TradeOpportunity } from "../../decision-engine/types";
import type {
  AthenaStructuredContext,
  ChartAwareness,
  ExplainTarget,
} from "../types";
import {
  computeAtr,
  computeMacd,
  computeRsi,
  computeVwap,
} from "../../engine/indicators/calculations";
import type { Candlestick } from "../../types";

export interface ContextBuilderInput {
  analysis: AnalysisSnapshot | null;
  opportunity: TradeOpportunity | null;
  candles: Candlestick[];
  awareness: ChartAwareness;
  selectedObject?: ExplainTarget | null;
  recentDecisionLabels?: string[];
  news?: AthenaStructuredContext["news"];
  positions?: AthenaStructuredContext["positions"];
  journalNotes?: string[];
  preferences?: Record<string, string | number | boolean>;
}

/**
 * Builds compact structured context for GPT.
 * Never includes raw candle OHLC series.
 */
export function buildAthenaContext(
  input: ContextBuilderInput,
): AthenaStructuredContext {
  const { analysis, opportunity, candles, awareness } = input;
  const dataGaps: string[] = [];
  if (!analysis) dataGaps.push("intelligence_snapshot");
  if (!opportunity) dataGaps.push("decision_opportunity");
  if (!candles.length) dataGaps.push("candle_series");

  const closes = candles.map((c) => c.close);
  const last = candles.length - 1;
  const rsi = last >= 0 ? lastFinite(computeRsi(closes)) : null;
  const macd = last >= 0 ? lastFinite(computeMacd(closes).hist) : null;
  const atr = last >= 0 ? lastFinite(computeAtr(candles)) : null;
  const vwap = last >= 0 ? lastFinite(computeVwap(candles)) : null;
  const close = last >= 0 ? candles[last].close : null;
  const vwapBias =
    vwap != null && close != null
      ? close > vwap
        ? "above"
        : close < vwap
          ? "below"
          : "at"
      : null;

  const structureLabels =
    analysis?.structure.slice(-6).map((s) => `${s.label}:${s.direction}`) ?? [];

  const vol = analysis?.volume;
  const volumeFlags = vol
    ? [
        vol.absorption && "absorption",
        vol.exhaustion && "exhaustion",
        vol.climax && "climax",
        vol.divergence && "divergence",
      ].filter(Boolean) as string[]
    : [];

  return {
    symbol: awareness.symbol || analysis?.symbol || "—",
    timeframe: awareness.timeframe || analysis?.timeframe || "—",
    trend: {
      classification: analysis?.trend.classification ?? "unknown",
      direction: analysis?.trend.direction ?? "neutral",
      confidence: analysis?.trend.confidence ?? 0,
    },
    structure: {
      latestLabels: structureLabels,
      bias: structureBias(structureLabels),
    },
    liquidity: (analysis?.liquidity.slice(0, 5) ?? []).map((l) => ({
      kind: l.kind,
      importance: Math.round(l.importance),
      price: l.price,
    })),
    orderBlocks: (analysis?.orderBlocks.filter((o) => o.status === "active").slice(0, 4) ?? []).map(
      (o) => ({
        bias: o.bias,
        score: Math.round(o.score),
        top: o.top,
        bottom: o.bottom,
      }),
    ),
    fvgs: (analysis?.fvgs
      .filter((f) => f.status === "active" || f.status === "partial")
      .slice(0, 4) ?? []
    ).map((f) => ({
      bias: f.bias,
      status: f.status,
      fillRatio: Math.round(f.fillRatio * 100) / 100,
    })),
    volume: {
      participation: vol?.participation ?? "unknown",
      pressure: vol?.pressure ?? "unknown",
      flags: volumeFlags,
    },
    sessions: (analysis?.sessions.slice(0, 4) ?? []).map((s) => ({
      name: s.name,
      active: s.active,
      killZone: s.killZone,
    })),
    confluence: {
      bullish: Math.round(analysis?.confluence.bullishScore ?? 0),
      bearish: Math.round(analysis?.confluence.bearishScore ?? 0),
      neutral: Math.round(analysis?.confluence.neutralScore ?? 0),
      confidence: Math.round(analysis?.confluence.overallConfidence ?? 0),
      drivers: (analysis?.confluence.drivers.slice(0, 5) ?? []).map((d) => d.source),
    },
    opportunity: opportunity
      ? {
          bias: opportunity.bias,
          grade: opportunity.grade,
          confidence: Math.round(opportunity.confidence.score),
          confidenceLabel: opportunity.confidence.label,
          probability: {
            bullish: Math.round(opportunity.probability.bullish),
            bearish: Math.round(opportunity.probability.bearish),
            neutral: Math.round(opportunity.probability.neutral),
          },
          direction: opportunity.direction,
          entry:
            opportunity.direction !== "flat"
              ? opportunity.activeEntry.entry
              : undefined,
          stopLoss:
            opportunity.direction !== "flat"
              ? opportunity.activeEntry.stopLoss
              : undefined,
          takeProfit1:
            opportunity.direction !== "flat"
              ? opportunity.activeEntry.takeProfit1
              : undefined,
          takeProfit2:
            opportunity.direction !== "flat"
              ? opportunity.activeEntry.takeProfit2
              : undefined,
          takeProfit3:
            opportunity.direction !== "flat"
              ? opportunity.activeEntry.takeProfit3
              : undefined,
          riskReward:
            opportunity.direction !== "flat"
              ? opportunity.activeEntry.riskReward
              : undefined,
          riskCategory: opportunity.risk.category,
          supporting: opportunity.supportingSignals.slice(0, 6).map((s) => s.label),
          opposing: opportunity.opposingSignals.slice(0, 5).map((s) => s.label),
          explanationSummary: opportunity.explanation.summary,
          explanationReasons: opportunity.explanation.reasons.slice(0, 6),
          explanationRisks: opportunity.explanation.risks.slice(0, 4),
          exitAction: opportunity.exit.action,
          exitReason: opportunity.exit.reason,
          mtfAlignment: opportunity.mtf.alignmentScore,
          mtfConflict: opportunity.mtf.conflictScore,
          mtfDominant: opportunity.mtf.dominantBias,
        }
      : null,
    indicators: { rsi, macdHist: macd, vwapBias, atr },
    awareness,
    selectedObject: input.selectedObject ?? null,
    recentDecisions: (input.recentDecisionLabels ?? []).slice(-8),
    news: input.news?.slice(0, 3),
    positions: input.positions?.slice(0, 5),
    journalNotes: input.journalNotes?.slice(-3),
    preferences: input.preferences,
    dataGaps,
  };
}

function structureBias(labels: string[]): string {
  const bull = labels.filter((l) => l.includes("bullish")).length;
  const bear = labels.filter((l) => l.includes("bearish")).length;
  if (bull > bear) return "bullish";
  if (bear > bull) return "bearish";
  return "neutral";
}

function lastFinite(arr: Array<number | null | undefined>): number | null {
  for (let i = arr.length - 1; i >= 0; i--) {
    const v = arr[i];
    if (v != null && Number.isFinite(v)) return Math.round(v * 10000) / 10000;
  }
  return null;
}

export function contextHash(ctx: AthenaStructuredContext): string {
  return [
    ctx.symbol,
    ctx.timeframe,
    ctx.trend.classification,
    ctx.opportunity?.bias,
    ctx.opportunity?.confidence,
    ctx.opportunity?.grade,
    ctx.confluence.confidence,
    ctx.selectedObject?.kind,
    ctx.selectedObject?.label,
  ].join("|");
}
