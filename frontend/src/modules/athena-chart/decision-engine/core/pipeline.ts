/**
 * Decision pipeline — deterministic, no GPT.
 * Collect → Normalize → Score → Confidence → Opportunity → Risk → Explain → Publish
 */

import type { Candlestick } from "../../types";
import type { AnalysisSnapshot } from "../../intelligence/types";
import type {
  DecisionEvent,
  DecisionInput,
  DecisionMemoryRecord,
  DecisionSnapshot,
  TradeOpportunity,
} from "../types";
import { collectNormalizedSignals, partitionSignals } from "./collectSignals";
import { computeConfidence } from "./confidence";
import { computeProbabilities } from "./probability";
import { voteMultiTimeframe } from "./mtfVoting";
import {
  classifyOpportunity,
  directionOf,
  gradeTrade,
} from "./opportunity";
import {
  generateEntries,
  meetsRrFilter,
  pickActiveEntry,
  zonesFromAnalysis,
} from "./entry";
import { evaluateExit } from "./exit";
import { assessRisk } from "./risk";
import { buildExplanation } from "./explain";
import { resolveProfile } from "../strategies/profiles";
import { stableId, uid } from "../utils/math";
import { candleTimeSec } from "../../utils/format";

export function hashDecisionInput(
  analysis: AnalysisSnapshot,
  settingsKey: string,
): string {
  return [
    analysis.symbol,
    analysis.timeframe,
    analysis.candleCount,
    analysis.lastTime,
    Math.round(analysis.confluence.overallConfidence),
    analysis.trend.classification,
    analysis.structure.length,
    analysis.orderBlocks.length,
    analysis.fvgs.length,
    settingsKey,
  ].join("|");
}

export function runDecisionPipeline(input: DecisionInput): {
  snapshot: DecisionSnapshot;
  memory: DecisionMemoryRecord[];
} {
  const { candles, symbol, timeframe, analysis, settings, previousOpportunity } =
    input;
  const profile = resolveProfile(settings);
  const settingsKey = JSON.stringify({
    strategy: settings.strategy,
    riskMode: settings.riskMode,
    entryStyle: settings.entryStyle,
    minConfidence: settings.minConfidence,
    minRiskReward: settings.minRiskReward,
    weights: settings.signalWeights,
  });
  const inputHash = hashDecisionInput(analysis, settingsKey);
  const memory: DecisionMemoryRecord[] = [];
  const events: DecisionEvent[] = [];
  const now = Date.now();
  const lastCandle = candles[candles.length - 1];
  const time = lastCandle?.time ?? new Date().toISOString();
  const timeSec = lastCandle ? candleTimeSec(lastCandle.time) : now / 1000;

  // 1-3 Collect / normalize / score
  const signals = collectNormalizedSignals(analysis, candles, settings);

  // MTF voting
  const mtf = voteMultiTimeframe(analysis);

  // Probabilities
  const probability = computeProbabilities(
    signals,
    analysis.confluence.bullishScore,
    analysis.confluence.bearishScore,
    analysis.confluence.neutralScore,
  );

  const dominant =
    probability.bullish >= probability.bearish &&
    probability.bullish >= probability.neutral
      ? "bullish"
      : probability.bearish >= probability.bullish &&
          probability.bearish >= probability.neutral
        ? "bearish"
        : "neutral";

  const { supporting, opposing } = partitionSignals(signals, dominant);
  const confidence = computeConfidence(signals, analysis, dominant);

  let bias = classifyOpportunity(
    probability,
    confidence,
    mtf,
    profile.confidenceThreshold,
  );
  let direction = directionOf(bias);

  // Entries / risk / grade
  let entries = generateEntries(candles, analysis, direction, settings);
  let activeEntry = pickActiveEntry(entries, settings.entryStyle);

  // Filter by min RR — downgrade to watch/neutral if fails
  if (
    activeEntry &&
    direction !== "flat" &&
    !meetsRrFilter(activeEntry, profile.minRiskReward)
  ) {
    if (bias === "strong_buy") bias = "watch_buy";
    else if (bias === "buy") bias = "watch_buy";
    else if (bias === "strong_sell") bias = "watch_sell";
    else if (bias === "sell") bias = "watch_sell";
    else if (bias !== "watch_buy" && bias !== "watch_sell") {
      bias = "neutral";
      direction = "flat";
      entries = [];
      activeEntry = null;
    }
  }

  // Confidence gate
  if (confidence.score < profile.confidenceThreshold && direction !== "flat") {
    if (bias === "strong_buy" || bias === "buy") bias = "watch_buy";
    else if (bias === "strong_sell" || bias === "sell") bias = "watch_sell";
  }

  const atrSig = signals.find((s) => s.source === "atr");
  const volPenalty = atrSig?.strength ?? 40;
  const sessionActive = analysis.sessions.some((s) => s.active);

  const placeholderRr = activeEntry?.riskReward ?? 0;
  const { grade, qualityScore } = gradeTrade({
    confidence: confidence.score,
    riskReward: placeholderRr,
    mtfAlignment: mtf.alignmentScore,
    supportCount: supporting.length,
    opposeCount: opposing.length,
    sessionActive,
    volatilityPenalty: volPenalty,
  });

  const risk = activeEntry
    ? assessRisk(candles, activeEntry, settings, confidence.score, mtf.conflictScore)
    : {
        maximumRisk: 0,
        expectedDrawdown: 0,
        positionSize: 0,
        atrRisk: 0,
        recommendedLeverage: 1,
        expectedHoldingBars: profile.holdingBarsHint,
        category: "low" as const,
      };

  const { buyZone, sellZone } = zonesFromAnalysis(analysis, direction);

  const explanation = buildExplanation({
    bias,
    grade,
    confidence,
    supporting,
    opposing,
    rr: placeholderRr,
  });

  // Expiry based on strategy holding hint
  const barMs = estimateBarMs(timeframe);
  const expiresAt = now + profile.holdingBarsHint * barMs;

  let opportunity: TradeOpportunity | null = null;

  if (direction !== "flat" && activeEntry && grade !== "Avoid") {
    const prevId =
      previousOpportunity &&
      previousOpportunity.direction === direction &&
      previousOpportunity.status === "active"
        ? previousOpportunity.id
        : stableId("opp", symbol, timeframe, direction, bias, Math.round(confidence.score / 5));

    opportunity = {
      id: prevId,
      symbol,
      timeframe,
      bias,
      direction,
      confidence,
      qualityScore,
      grade,
      probability,
      entries,
      activeEntry,
      risk,
      exit: { action: "hold", reason: "New setup" },
      mtf,
      supportingSignals: supporting.slice(0, 10),
      opposingSignals: opposing.slice(0, 8),
      buyZone,
      sellZone,
      explanation,
      expiresAt,
      createdAt: previousOpportunity?.id === prevId ? previousOpportunity.createdAt : now,
      updatedAt: now,
      status: "active",
    };

    // Exit monitoring against previous / current
    const exit = evaluateExit(candles, analysis, opportunity);
    opportunity = { ...opportunity, exit };

    if (exit.action === "close_trade") {
      opportunity = { ...opportunity, status: "closed" };
      pushEvent(events, {
        id: uid("evt"),
        time,
        timeSec,
        label: `Close Trade — ${exit.reason}`,
        kind: "close",
        confidence: confidence.score,
        grade,
        bias: dominant,
        opportunityId: opportunity.id,
      });
      memory.push({
        id: uid("mem"),
        at: now,
        type: "exit_action",
        opportunityId: opportunity.id,
        payload: { action: exit.action, reason: exit.reason },
      });
    } else if (exit.action === "partial_exit") {
      opportunity = {
        ...opportunity,
        status: "tp1",
        activeEntry:
          exit.suggestedStop != null
            ? { ...opportunity.activeEntry, stopLoss: exit.suggestedStop }
            : opportunity.activeEntry,
      };
      pushEvent(events, {
        id: uid("evt"),
        time,
        timeSec,
        label: `TP1 / Partial — ${exit.reason}`,
        kind: "tp_reached",
        confidence: confidence.score,
        grade,
        bias: dominant,
        opportunityId: opportunity.id,
      });
      memory.push({
        id: uid("mem"),
        at: now,
        type: "tp_hit",
        opportunityId: opportunity.id,
        payload: { level: "tp1", reason: exit.reason },
      });
    } else if (exit.action === "move_stop_loss" && exit.suggestedStop != null) {
      opportunity = {
        ...opportunity,
        status: "tp2",
        activeEntry: {
          ...opportunity.activeEntry,
          stopLoss: exit.suggestedStop,
        },
      };
      pushEvent(events, {
        id: uid("evt"),
        time,
        timeSec,
        label: `Move SL → ${exit.suggestedStop}`,
        kind: "sl_move",
        confidence: confidence.score,
        grade,
        bias: dominant,
        opportunityId: opportunity.id,
      });
      memory.push({
        id: uid("mem"),
        at: now,
        type: "exit_action",
        opportunityId: opportunity.id,
        payload: { action: "move_stop_loss", stop: exit.suggestedStop },
      });
    }

    // Confidence change events
    if (
      previousOpportunity &&
      previousOpportunity.id === opportunity.id &&
      Math.abs(previousOpportunity.confidence.score - confidence.score) >= 4
    ) {
      pushEvent(events, {
        id: uid("evt"),
        time,
        timeSec,
        label: `Confidence ${Math.round(previousOpportunity.confidence.score)}→${Math.round(confidence.score)}`,
        kind: "confidence_change",
        confidence: confidence.score,
        grade,
        bias: dominant,
        opportunityId: opportunity.id,
      });
      memory.push({
        id: uid("mem"),
        at: now,
        type: "confidence_change",
        opportunityId: opportunity.id,
        payload: {
          from: previousOpportunity.confidence.score,
          to: confidence.score,
        },
      });
    }

    if (!previousOpportunity || previousOpportunity.id !== opportunity.id) {
      pushEvent(events, {
        id: uid("evt"),
        time,
        timeSec,
        label: `${formatBias(bias)} Opportunity · Grade ${grade}`,
        kind: "opportunity",
        confidence: confidence.score,
        grade,
        bias: dominant,
        opportunityId: opportunity.id,
      });
      memory.push({
        id: uid("mem"),
        at: now,
        type: "opportunity_created",
        opportunityId: opportunity.id,
        payload: {
          bias,
          grade,
          confidence: confidence.score,
          entry: activeEntry.entry,
          sl: activeEntry.stopLoss,
          tp1: activeEntry.takeProfit1,
        },
      });
    } else {
      memory.push({
        id: uid("mem"),
        at: now,
        type: "opportunity_updated",
        opportunityId: opportunity.id,
        payload: { bias, grade, confidence: confidence.score },
      });
    }
  } else if (previousOpportunity?.status === "active") {
    // Cancel prior if no longer valid
    pushEvent(events, {
      id: uid("evt"),
      time,
      timeSec,
      label: "Opportunity cancelled",
      kind: "cancel",
      confidence: confidence.score,
      bias: dominant,
      opportunityId: previousOpportunity.id,
    });
    memory.push({
      id: uid("mem"),
      at: now,
      type: "opportunity_cancelled",
      opportunityId: previousOpportunity.id,
      payload: { reason: "filters_failed", grade },
    });
  }

  // Neutral snapshot still useful for panel (probabilities etc.)
  if (!opportunity) {
    opportunity = buildNeutralOpportunity({
      symbol,
      timeframe,
      confidence,
      probability,
      mtf,
      supporting,
      opposing,
      explanation: buildExplanation({
        bias: "neutral",
        grade: grade === "Avoid" ? "Avoid" : "C",
        confidence,
        supporting,
        opposing,
        rr: 0,
      }),
      risk,
      buyZone,
      sellZone,
      now,
      expiresAt,
      previousId: previousOpportunity?.direction === "flat" ? previousOpportunity.id : undefined,
    });
  }

  return {
    snapshot: {
      symbol,
      timeframe,
      opportunity,
      signals,
      events,
      analyzedAt: now,
      inputHash,
    },
    memory,
  };
}

function buildNeutralOpportunity(p: {
  symbol: string;
  timeframe: string;
  confidence: TradeOpportunity["confidence"];
  probability: TradeOpportunity["probability"];
  mtf: TradeOpportunity["mtf"];
  supporting: TradeOpportunity["supportingSignals"];
  opposing: TradeOpportunity["opposingSignals"];
  explanation: TradeOpportunity["explanation"];
  risk: TradeOpportunity["risk"];
  buyZone: TradeOpportunity["buyZone"];
  sellZone: TradeOpportunity["sellZone"];
  now: number;
  expiresAt: number;
  previousId?: string;
}): TradeOpportunity {
  const flatEntry = {
    style: "balanced" as const,
    entry: 0,
    stopLoss: 0,
    takeProfit1: 0,
    takeProfit2: 0,
    takeProfit3: 0,
    riskReward: 0,
    atrDistance: 0,
    maximumRisk: 0,
  };
  return {
    id: p.previousId ?? uid("opp"),
    symbol: p.symbol,
    timeframe: p.timeframe,
    bias: "neutral",
    direction: "flat",
    confidence: p.confidence,
    qualityScore: p.confidence.score * 0.5,
    grade: "C",
    probability: p.probability,
    entries: [],
    activeEntry: flatEntry,
    risk: p.risk,
    exit: { action: "hold", reason: "No trade" },
    mtf: p.mtf,
    supportingSignals: p.supporting.slice(0, 8),
    opposingSignals: p.opposing.slice(0, 6),
    buyZone: p.buyZone,
    sellZone: p.sellZone,
    explanation: p.explanation,
    expiresAt: p.expiresAt,
    createdAt: p.now,
    updatedAt: p.now,
    status: "active",
  };
}

function pushEvent(events: DecisionEvent[], e: DecisionEvent): void {
  events.push(e);
}

function formatBias(bias: string): string {
  return bias
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function estimateBarMs(tf: string): number {
  const t = tf.toUpperCase();
  if (t === "1M" || t === "M1") return 60_000;
  if (t === "5M" || t === "M5") return 300_000;
  if (t === "15M" || t === "M15") return 900_000;
  if (t === "1H" || t === "H1") return 3_600_000;
  if (t === "4H" || t === "H4") return 14_400_000;
  if (t === "D1" || t === "1D" || t === "DAILY") return 86_400_000;
  return 300_000;
}

/** Cheap candle fingerprint for incremental skip (shared with service). */
export function hashCandlesLight(candles: Candlestick[]): string {
  if (!candles.length) return "empty";
  const a = candles[0];
  const b = candles[candles.length - 1];
  return `${candles.length}:${a.time}:${b.time}:${b.close}:${b.tick_volume ?? 0}`;
}
