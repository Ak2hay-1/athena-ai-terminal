import type { Candlestick } from "../../types";
import type {
  AnalysisInput,
  AnalysisSnapshot,
  IntelligenceEvent,
  IntelligenceSettings,
  MtfAlignment,
} from "../types";
import { detectSwings } from "../detectors/swing";
import { detectStructure } from "../detectors/structure";
import { classifyTrend } from "../detectors/trend";
import { detectSupportResistance } from "../detectors/sr";
import { detectSupplyDemand } from "../detectors/supplyDemand";
import { detectOrderBlocks } from "../detectors/orderBlock";
import { detectFairValueGaps } from "../detectors/fvg";
import { detectLiquidity } from "../detectors/liquidity";
import { detectImbalances } from "../detectors/imbalance";
import { computePremiumDiscount } from "../detectors/premium";
import { detectSessions } from "../detectors/session";
import { analyzeVolume } from "../detectors/volume";
import { detectPatterns } from "../detectors/patterns";
import { computeConfluence } from "../detectors/confluence";
import { makeId } from "../utils/scoring";
import { candleTimeSec } from "../../utils/format";

/** Deterministic analysis pipeline — each stage independent. */
export function runAnalysisPipeline(input: AnalysisInput): AnalysisSnapshot {
  const { candles, symbol, timeframe, settings } = input;
  const series =
    settings.performanceMode === "fast" && candles.length > 400
      ? candles.slice(-400)
      : candles;

  const swings = detectSwings(series, settings);
  const structure = detectStructure(series, swings);
  const trend = classifyTrend(swings, structure);
  const levels = detectSupportResistance(series, swings, settings);
  const zones = detectSupplyDemand(series);
  const orderBlocks = detectOrderBlocks(series);
  const fvgs = detectFairValueGaps(series);
  const liquidity = detectLiquidity(series, swings);
  const imbalances =
    settings.performanceMode === "full" ? detectImbalances(series) : [];
  const premiumDiscount = computePremiumDiscount(swings);
  const sessions = detectSessions(series);
  const volume = analyzeVolume(series);
  const patterns = detectPatterns(series, swings);

  const partial = {
    symbol,
    timeframe,
    candleCount: series.length,
    lastTime: series[series.length - 1]?.time ?? "",
    swings,
    structure,
    trend,
    levels,
    zones,
    orderBlocks,
    fvgs,
    liquidity,
    imbalances,
    premiumDiscount,
    sessions,
    volume,
    patterns,
  };

  const confluence = computeConfluence(partial, settings);
  const events = buildEvents(partial, confluence);
  const mtf = input.multiTimeframe
    ? analyzeMultiTimeframe(input.multiTimeframe, settings)
    : null;

  return {
    ...partial,
    confluence,
    events,
    mtf,
    analyzedAt: Date.now(),
  };
}

function buildEvents(
  snap: Omit<AnalysisSnapshot, "confluence" | "events" | "mtf" | "analyzedAt">,
  confluence: AnalysisSnapshot["confluence"],
): IntelligenceEvent[] {
  const events: IntelligenceEvent[] = [];
  const push = (
    label: string,
    kind: string,
    time: string,
    confidence: number,
    bias?: IntelligenceEvent["bias"],
  ) => {
    events.push({
      id: makeId("ev-"),
      time,
      timeSec: candleTimeSec(time),
      label,
      kind,
      confidence,
      bias,
    });
  };

  for (const s of snap.structure.filter((x) => x.label === "BOS" || x.label === "CHOCH").slice(-4)) {
    push(
      `${s.direction === "bullish" ? "Bullish" : "Bearish"} ${s.label}`,
      s.label,
      s.time,
      s.confidence,
      s.direction,
    );
  }
  for (const z of snap.zones.filter((z) => z.status === "active").slice(-3)) {
    push(
      `${z.kind === "demand" ? "Demand" : "Supply"} Zone`,
      "zone",
      snap.lastTime,
      z.confidence,
      z.kind === "demand" ? "bullish" : "bearish",
    );
  }
  for (const l of snap.liquidity.filter((x) => x.kind === "sweep").slice(-3)) {
    push("Liquidity Sweep", "liquidity", l.time, l.confidence, "neutral");
  }
  for (const ob of snap.orderBlocks.filter((o) => o.status === "active").slice(-2)) {
    push(
      `${ob.bias === "bullish" ? "Bullish" : "Bearish"} Order Block`,
      "order_block",
      snap.lastTime,
      ob.confidence,
      ob.bias,
    );
  }
  push(
    `Confluence Score ${Math.round(confluence.overallConfidence)}`,
    "confluence",
    snap.lastTime,
    confluence.overallConfidence,
    confluence.bullishScore >= confluence.bearishScore ? "bullish" : "bearish",
  );

  return events.sort((a, b) => a.timeSec - b.timeSec).slice(-40);
}

export function analyzeMultiTimeframe(
  frames: Array<{ timeframe: string; candles: Candlestick[] }>,
  settings: IntelligenceSettings,
): MtfAlignment {
  const biases = frames.map(({ timeframe, candles }) => {
    const swings = detectSwings(candles, settings);
    const structure = detectStructure(candles, swings);
    const trend = classifyTrend(swings, structure);
    return {
      timeframe,
      classification: trend.classification,
      confidence: trend.confidence,
    };
  });

  const bullish = biases.filter((b) => b.classification.includes("bull")).length;
  const bearish = biases.filter((b) => b.classification.includes("bear")).length;
  const agreementPct = Math.round(
    (Math.max(bullish, bearish) / Math.max(1, biases.length)) * 100,
  );
  const dominant =
    bullish > bearish
      ? biases.find((b) => b.classification.includes("bull"))?.classification ?? "range"
      : bearish > bullish
        ? biases.find((b) => b.classification.includes("bear"))?.classification ?? "range"
        : ("range" as const);

  return { frames: biases, agreementPct, dominant };
}

export function hashCandles(candles: Candlestick[]): string {
  if (!candles.length) return "0";
  const first = candles[0];
  const last = candles[candles.length - 1];
  return `${candles.length}:${first.time}:${last.time}:${last.close}:${last.tick_volume}`;
}
