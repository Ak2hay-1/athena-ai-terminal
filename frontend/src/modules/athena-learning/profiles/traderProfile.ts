import type {
  RiskMode,
  TraderProfile,
  TradeLearningRecord,
} from "../types";
import { round, winRate } from "../utils/math";

export function buildTraderProfile(
  userId: string,
  trades: TradeLearningRecord[],
): TraderProfile {
  const closed = trades.filter((t) => t.outcome === "win" || t.outcome === "loss");
  const wins = closed.filter((t) => t.outcome === "win");

  const sessionStats: TraderProfile["sessionStats"] = {};
  const pairStats: TraderProfile["pairStats"] = {};
  const timeframeStats: TraderProfile["timeframeStats"] = {};
  const modeCount: Record<RiskMode, number> = {
    conservative: 0,
    balanced: 0,
    aggressive: 0,
  };

  for (const t of closed) {
    const session = t.session || "unknown";
    const ss = sessionStats[session] ?? { trades: 0, winRate: 0 };
    ss.trades += 1;
    sessionStats[session] = ss;

    const ps = pairStats[t.symbol] ?? { trades: 0, winRate: 0, avgRr: 0 };
    ps.trades += 1;
    ps.avgRr += t.realizedRr;
    pairStats[t.symbol] = ps;

    const tf = timeframeStats[t.timeframe] ?? { trades: 0, winRate: 0 };
    tf.trades += 1;
    timeframeStats[t.timeframe] = tf;

    modeCount[t.riskMode] += 1;
  }

  // finalize win rates
  for (const t of closed) {
    const session = t.session || "unknown";
    if (t.outcome === "win") {
      const s = sessionStats[session];
      if (s) s.winRate += 1;
      const p = pairStats[t.symbol];
      if (p) p.winRate += 1;
      const tf = timeframeStats[t.timeframe];
      if (tf) tf.winRate += 1;
    }
  }
  for (const k of Object.keys(sessionStats)) {
    const s = sessionStats[k];
    s.winRate = winRate(s.winRate, s.trades);
  }
  for (const k of Object.keys(pairStats)) {
    const p = pairStats[k];
    const winsN = p.winRate;
    p.avgRr = p.trades ? round(p.avgRr / p.trades, 2) : 0;
    p.winRate = winRate(winsN, p.trades);
  }
  for (const k of Object.keys(timeframeStats)) {
    const tf = timeframeStats[k];
    tf.winRate = winRate(tf.winRate, tf.trades);
  }

  const bestSession =
    Object.entries(sessionStats).sort((a, b) => b[1].winRate - a[1].winRate)[0]?.[0] ??
    "—";
  const weakestSession =
    Object.entries(sessionStats)
      .filter(([, v]) => v.trades >= 2)
      .sort((a, b) => a[1].winRate - b[1].winRate)[0]?.[0] ?? "—";
  const bestPair =
    Object.entries(pairStats).sort((a, b) => b[1].winRate - a[1].winRate)[0]?.[0] ?? "—";
  const weakestPair =
    Object.entries(pairStats)
      .filter(([, v]) => v.trades >= 2)
      .sort((a, b) => a[1].winRate - b[1].winRate)[0]?.[0] ?? "—";
  const bestTimeframe =
    Object.entries(timeframeStats).sort((a, b) => b[1].winRate - a[1].winRate)[0]?.[0] ??
    "—";

  const wr = winRate(wins.length, closed.length);
  const avgRr = closed.length
    ? round(closed.reduce((s, t) => s + t.realizedRr, 0) / closed.length, 2)
    : 0;
  const avgHold = closed.length
    ? round(closed.reduce((s, t) => s + t.holdMinutes, 0) / closed.length, 1)
    : 0;

  const preferredRiskMode = (Object.entries(modeCount).sort(
    (a, b) => b[1] - a[1],
  )[0]?.[0] ?? "balanced") as RiskMode;

  const coachScore = round(
    Math.min(100, wr * 0.5 + Math.min(avgRr, 3) * 15 + Math.min(closed.length, 50) * 0.4),
    1,
  );
  const consistencyScore = round(
    Math.min(
      100,
      Object.values(sessionStats).length
        ? 100 -
          Math.max(
            ...Object.values(sessionStats).map((s) => Math.abs(s.winRate - wr)),
          ) *
            0.8
        : 50,
    ),
    1,
  );

  return {
    userId,
    updatedAt: Date.now(),
    bestSession,
    weakestSession,
    bestPair,
    weakestPair,
    bestTimeframe,
    avgHoldMinutes: avgHold,
    winRate: wr,
    avgRiskPct: 0.8,
    avgRr,
    totalTrades: closed.length,
    coachScore,
    consistencyScore,
    preferredRiskMode,
    sessionStats,
    pairStats,
    timeframeStats,
  };
}
