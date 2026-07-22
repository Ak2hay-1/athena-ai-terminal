import type { StrategyKind, StrategyPerformance, TradeLearningRecord } from "../types";
import { expectancy, maxDrawdown, profitFactor, round, winRate } from "../utils/math";

export function computeStrategyPerformance(
  trades: TradeLearningRecord[],
): StrategyPerformance[] {
  const kinds: StrategyKind[] = ["scalping", "intraday", "swing", "position"];
  return kinds.map((strategy) => {
    const list = trades.filter(
      (t) => t.strategy === strategy && (t.outcome === "win" || t.outcome === "loss"),
    );
    const wins = list.filter((t) => t.outcome === "win");
    const losses = list.filter((t) => t.outcome === "loss");
    const grossWin = wins.reduce((s, t) => s + Math.max(0, t.pnl), 0);
    const grossLoss = losses.reduce((s, t) => s + Math.abs(Math.min(0, t.pnl)), 0);
    const avgWin = wins.length ? grossWin / wins.length : 0;
    const avgLoss = losses.length ? grossLoss / losses.length : 0;
    const wr = winRate(wins.length, list.length);
    const avgRr = list.length
      ? round(list.reduce((s, t) => s + t.realizedRr, 0) / list.length, 2)
      : 0;
    const avgHold = list.length
      ? round(list.reduce((s, t) => s + t.holdMinutes, 0) / list.length, 1)
      : 0;

    return {
      strategy,
      trades: list.length,
      wins: wins.length,
      losses: losses.length,
      winRate: wr,
      avgRr,
      maxDrawdown: maxDrawdown(list.map((t) => t.pnl)),
      profitFactor: profitFactor(grossWin, grossLoss),
      expectancy: expectancy(wr, avgWin, avgLoss),
      avgHoldMinutes: avgHold,
      sharpe: null,
      sortino: null,
    };
  });
}

export function compareStrategies(
  a: StrategyPerformance,
  b: StrategyPerformance,
): Array<{ metric: string; a: number; b: number; winner: "A" | "B" | "tie" }> {
  const rows: Array<{ metric: string; a: number; b: number }> = [
    { metric: "Win Rate", a: a.winRate, b: b.winRate },
    { metric: "Profit Factor", a: a.profitFactor, b: b.profitFactor },
    { metric: "Avg RR", a: a.avgRr, b: b.avgRr },
    { metric: "Drawdown", a: a.maxDrawdown, b: b.maxDrawdown },
    { metric: "Avg Hold (min)", a: a.avgHoldMinutes, b: b.avgHoldMinutes },
    { metric: "Expectancy", a: a.expectancy, b: b.expectancy },
  ];
  return rows.map((r) => {
    const lowerBetter = r.metric === "Drawdown" || r.metric.includes("Hold");
    let winner: "A" | "B" | "tie" = "tie";
    if (Math.abs(r.a - r.b) > 0.01) {
      if (lowerBetter) winner = r.a < r.b ? "A" : "B";
      else winner = r.a > r.b ? "A" : "B";
    }
    return { ...r, winner };
  });
}
