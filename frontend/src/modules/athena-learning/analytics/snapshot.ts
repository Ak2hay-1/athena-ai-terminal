import type {
  AnalyticsSnapshot,
  TradeEvaluation,
  TradeLearningRecord,
  TraderProfile,
} from "../types";
import {
  expectancy,
  maxDrawdown,
  profitFactor,
  round,
  weekKey,
  winRate,
} from "../utils/math";

export function buildAnalyticsSnapshot(
  trades: TradeLearningRecord[],
  evaluations: TradeEvaluation[],
  profile: TraderProfile | null,
): AnalyticsSnapshot {
  const closed = trades.filter((t) => t.outcome === "win" || t.outcome === "loss");
  const wins = closed.filter((t) => t.outcome === "win");
  const losses = closed.filter((t) => t.outcome === "loss");
  const grossWin = wins.reduce((s, t) => s + Math.max(0, t.pnl), 0);
  const grossLoss = losses.reduce((s, t) => s + Math.abs(Math.min(0, t.pnl)), 0);
  const wr = winRate(wins.length, closed.length);
  const avgWin = wins.length ? grossWin / wins.length : 0;
  const avgLoss = losses.length ? grossLoss / losses.length : 0;
  const avgRr = closed.length
    ? round(closed.reduce((s, t) => s + t.realizedRr, 0) / closed.length, 2)
    : 0;
  const avgHold = closed.length
    ? round(closed.reduce((s, t) => s + t.holdMinutes, 0) / closed.length, 1)
    : 0;

  const decisionAccuracy = closed.length
    ? round(
        (closed.filter((t) => t.predictionCorrect).length / closed.length) * 100,
        1,
      )
    : 0;
  const confidenceAccuracy = evaluations.length
    ? round(
        evaluations.reduce((s, e) => s + e.confidenceAccuracy, 0) / evaluations.length,
        1,
      )
    : 0;

  const weeks = new Map<string, { wins: number; n: number; rr: number }>();
  for (const t of closed) {
    const w = weekKey(t.closedAt);
    const cur = weeks.get(w) ?? { wins: 0, n: 0, rr: 0 };
    cur.n += 1;
    cur.rr += t.realizedRr;
    if (t.outcome === "win") cur.wins += 1;
    weeks.set(w, cur);
  }

  return {
    winRate: wr,
    profitFactor: profitFactor(grossWin, grossLoss),
    expectancy: expectancy(wr, avgWin, avgLoss),
    avgRr,
    maxDrawdown: maxDrawdown(closed.map((t) => t.pnl)),
    avgHoldMinutes: avgHold,
    tradeCount: closed.length,
    decisionAccuracy,
    confidenceAccuracy,
    coachScore: profile?.coachScore ?? 0,
    consistencyScore: profile?.consistencyScore ?? 0,
    sessionPerformance: Object.entries(profile?.sessionStats ?? {}).map(
      ([session, v]) => ({
        session,
        winRate: v.winRate,
        trades: v.trades,
      }),
    ),
    pairPerformance: Object.entries(profile?.pairStats ?? {}).map(([symbol, v]) => ({
      symbol,
      winRate: v.winRate,
      trades: v.trades,
      avgRr: v.avgRr,
    })),
    weeklyTimeline: [...weeks.entries()]
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([week, v]) => ({
        week,
        winRate: winRate(v.wins, v.n),
        avgRr: round(v.rr / v.n, 2),
        trades: v.n,
      })),
  };
}
