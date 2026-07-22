import type {
  BrainSimilarHit,
  BrainSimilarQuery,
  MarketMemoryEvent,
  OutcomeLabel,
  TradeLearningRecord,
} from "../types";
import { uid } from "../utils/math";

/** Athena Brain — local historical similarity (not GPT). */
export function ingestMarketMemory(
  trade: TradeLearningRecord,
  tags: string[],
): MarketMemoryEvent {
  return {
    id: uid("mem"),
    at: trade.closedAt,
    userId: trade.userId,
    symbol: trade.symbol,
    timeframe: trade.timeframe,
    session: trade.session,
    tags: tags.length
      ? tags
      : [
          trade.bias,
          ...trade.supportingSignals.slice(0, 3).map((s) => s.toLowerCase().replace(/\s+/g, "_")),
        ],
    confidence: trade.confidenceAtEntry,
    outcome: trade.outcome,
    pnl: trade.pnl,
    contextHash: [
      trade.symbol,
      trade.timeframe,
      trade.session ?? "",
      trade.bias,
      Math.round(trade.confidenceAtEntry / 5),
    ].join("|"),
    extras: {
      grade: trade.grade ?? "",
      strategy: trade.strategy,
      rr: trade.realizedRr,
    },
  };
}

export function findSimilarSetups(
  memory: MarketMemoryEvent[],
  query: BrainSimilarQuery,
): BrainSimilarHit[] {
  const limit = query.limit ?? 50;
  const qTags = new Set(query.tags.map((t) => t.toLowerCase()));

  const scored = memory
    .filter((e) => {
      if (query.symbol && e.symbol !== query.symbol) return false;
      if (query.timeframe && e.timeframe !== query.timeframe) return false;
      if (query.session && e.session && e.session !== query.session) return false;
      return true;
    })
    .map((event) => {
      const overlap = event.tags.filter((t) => qTags.has(t.toLowerCase())).length;
      const tagScore = qTags.size ? overlap / qTags.size : 0.3;
      const similarity = Math.round(tagScore * 100);
      const reason = overlap
        ? `Matched tags: ${event.tags.filter((t) => qTags.has(t.toLowerCase())).join(", ")}`
        : "Contextual match on symbol/session filters";
      return { event, similarity, reason };
    })
    .filter((h) => h.similarity > 0 || !qTags.size)
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, limit);

  return scored;
}

export function patternSuccessRate(
  memory: MarketMemoryEvent[],
  tags: string[],
  session?: string,
): { rate: number; sample: number; wins: number } {
  const hits = findSimilarSetups(memory, { tags, session, limit: 500 });
  const closed = hits.filter(
    (h) => h.event.outcome === "win" || h.event.outcome === "loss",
  );
  const wins = closed.filter((h) => h.event.outcome === "win").length;
  return {
    rate: closed.length ? Math.round((wins / closed.length) * 1000) / 10 : 0,
    sample: closed.length,
    wins,
  };
}

export function summarizeOutcomeDistribution(
  hits: BrainSimilarHit[],
): Record<OutcomeLabel, number> {
  const dist: Record<OutcomeLabel, number> = {
    win: 0,
    loss: 0,
    breakeven: 0,
    cancelled: 0,
    unknown: 0,
  };
  for (const h of hits) dist[h.event.outcome] += 1;
  return dist;
}
