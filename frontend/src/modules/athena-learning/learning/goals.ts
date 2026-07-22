import type { Achievement, LearningGoal, TradeLearningRecord } from "../types";
import { dayKey, uid, winRate } from "../utils/math";

export function updateGoals(
  goals: LearningGoal[],
  trades: TradeLearningRecord[],
  dailyTradeCount: number,
): LearningGoal[] {
  const closed = trades.filter((t) => t.outcome === "win" || t.outcome === "loss");
  const wins = closed.filter((t) => t.outcome === "win").length;
  const wr = winRate(wins, closed.length);
  const avgRr = closed.length
    ? closed.reduce((s, t) => s + t.realizedRr, 0) / closed.length
    : 0;

  return goals.map((g) => {
    let current = g.current;
    if (g.metric === "win_rate") current = wr;
    if (g.metric === "avg_rr" || g.metric === "min_rr") current = Math.round(avgRr * 100) / 100;
    if (g.metric === "max_daily_trades") current = dailyTradeCount;
    if (g.metric === "max_risk_pct") current = 0.8;
    if (g.metric === "reduce_overtrading") {
      current = Math.max(0, g.target - Math.max(0, dailyTradeCount - 4));
    }
    const achieved =
      g.metric === "max_daily_trades" || g.metric === "max_risk_pct"
        ? current <= g.target
        : current >= g.target;
    return {
      ...g,
      current,
      achievedAt: achieved && !g.achievedAt ? Date.now() : g.achievedAt,
    };
  });
}

export function createGoal(
  title: string,
  metric: LearningGoal["metric"],
  target: number,
  unit: string,
): LearningGoal {
  return {
    id: uid("goal"),
    title,
    metric,
    target,
    current: 0,
    unit,
    createdAt: Date.now(),
  };
}

export function updateAchievements(
  achievements: Achievement[],
  trades: TradeLearningRecord[],
  revengeFreeDays: number,
  noStopMoveStreak: number,
): Achievement[] {
  const closed = trades.filter((t) => t.outcome === "win" || t.outcome === "loss");
  const winningDays = new Set<string>();
  const byDay = new Map<string, number>();
  for (const t of closed) {
    const d = dayKey(t.closedAt);
    byDay.set(d, (byDay.get(d) ?? 0) + t.pnl);
  }
  for (const [d, pnl] of byDay) {
    if (pnl > 0) winningDays.add(d);
  }

  // Perfect week check
  const weekAgo = Date.now() - 7 * 86400000;
  const weekTrades = closed.filter((t) => t.closedAt >= weekAgo);
  const weekWins = weekTrades.filter((t) => t.outcome === "win").length;
  const weekWr = winRate(weekWins, weekTrades.length);
  const weekRr = weekTrades.length
    ? weekTrades.reduce((s, t) => s + t.realizedRr, 0) / weekTrades.length
    : 0;
  const perfectWeek = weekTrades.length >= 5 && weekWr >= 60 && weekRr >= 1.5;

  return achievements.map((a) => {
    let progress = a.progress;
    if (a.code === "100_trades") progress = closed.length;
    if (a.code === "20_winning_days") progress = winningDays.size;
    if (a.code === "risk_discipline") progress = noStopMoveStreak;
    if (a.code === "no_revenge") progress = revengeFreeDays;
    if (a.code === "perfect_week") progress = perfectWeek ? 1 : 0;
    const unlocked =
      progress >= a.target ? a.unlockedAt ?? Date.now() : undefined;
    return { ...a, progress: Math.min(progress, a.target), unlockedAt: unlocked };
  });
}
