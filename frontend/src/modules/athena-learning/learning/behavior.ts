import type {
  BehaviorFlag,
  BehaviorReport,
  MistakeEvent,
  TradeLearningRecord,
} from "../types";
import { uid } from "../utils/math";

const MISTAKE_COPY: Record<
  BehaviorFlag,
  { description: (n: number) => string; impact: string; recommendation: string }
> = {
  fomo: {
    description: (n) => `FOMO entries detected ${n} time(s).`,
    impact: "Chasing often reduces RR and increases slippage vs planned entry.",
    recommendation: "Wait for Decision Engine entry zone; avoid market orders after impulse.",
  },
  revenge_trading: {
    description: (n) => `Revenge trading patterns after losses: ${n}.`,
    impact: "Post-loss size/frequency spikes degrade expectancy.",
    recommendation: "Enforce a cool-down of 1+ bars after a stop-out before next entry.",
  },
  overtrading: {
    description: (n) => `Overtrading days detected: ${n}.`,
    impact: "High frequency without edge increases costs and emotional errors.",
    recommendation: "Cap daily trades; prioritize A/A+ grades only.",
  },
  early_exit: {
    description: (n) => `Early exits before TP1: ${n}.`,
    impact: "Cutting winners early lowers average RR.",
    recommendation: "Scale out at TP1 only; journal emotional exits.",
  },
  late_exit: {
    description: (n) => `Late exits after thesis invalidation: ${n}.`,
    impact: "Holding losers past structure breaks deepens drawdowns.",
    recommendation: "Honor CHOCH/exit engine signals without delay.",
  },
  moving_stop_loss: {
    description: (n) => `You moved stop-loss ${n} time(s).`,
    impact: "Widening stops after entry typically enlarges losses.",
    recommendation: "Avoid moving stops once risk is defined (except to breakeven after TP1).",
  },
  cancelling_winners: {
    description: (n) => `Cancelled setups that later looked winning: ${n}.`,
    impact: "Skipping valid A-grade plans reduces sample of good expectancy trades.",
    recommendation: "Pre-commit to A/A+ setups during your best session.",
  },
  holding_losers: {
    description: (n) => `Holding losers beyond planned risk: ${n}.`,
    impact: "Asymmetric downside vs plan.",
    recommendation: "Hard stop discipline; no manual override past 1R.",
  },
  skipping_good_trades: {
    description: (n) => `Ignored high-confidence signals: ${n}.`,
    impact: "Missed edge when filters already passed.",
    recommendation: "Define a written checklist; execute when grade ≥ B+.",
  },
  chasing_price: {
    description: (n) => `Price chase entries: ${n}.`,
    impact: "Entries far from zone destroy RR.",
    recommendation: "Only enter inside Decision Engine buy/sell zone.",
  },
};

export function detectBehaviors(trades: TradeLearningRecord[]): BehaviorReport {
  const flags: BehaviorReport["flags"] = [];
  const byDay = new Map<string, number>();

  let stopMoves = 0;
  let earlyExits = 0;
  let lateLosses = 0;
  let revenge = 0;
  let ignored = 0;
  let chase = 0;

  const sorted = [...trades].sort((a, b) => a.closedAt - b.closedAt);
  for (let i = 0; i < sorted.length; i++) {
    const t = sorted[i];
    const day = new Date(t.closedAt).toISOString().slice(0, 10);
    byDay.set(day, (byDay.get(day) ?? 0) + 1);

    stopMoves += t.stopMoves;
    if (t.ignoredSignal) ignored += 1;
    if (t.result === "manual_exit" && t.outcome === "win" && t.realizedRr < t.plannedRr * 0.5) {
      earlyExits += 1;
    }
    if (t.outcome === "loss" && t.holdMinutes > 120 && t.realizedRr < -1.2) {
      lateLosses += 1;
    }
    if (
      i > 0 &&
      sorted[i - 1].outcome === "loss" &&
      t.openedAt - sorted[i - 1].closedAt < 15 * 60_000
    ) {
      revenge += 1;
    }
    // FOMO / chase: entry far from planned zone proxy — high confidence + loss + short hold
    if (t.confidenceAtEntry >= 80 && t.holdMinutes < 10 && t.outcome === "loss") {
      chase += 1;
    }
  }

  const overtradingDays = [...byDay.values()].filter((n) => n >= 6).length;

  const push = (
    flag: BehaviorFlag,
    count: number,
    severity: "low" | "medium" | "high",
    evidence: string,
  ) => {
    if (count <= 0) return;
    flags.push({ flag, count, severity, evidence });
  };

  push("moving_stop_loss", stopMoves, stopMoves > 10 ? "high" : "medium", `${stopMoves} stop moves`);
  push("early_exit", earlyExits, earlyExits > 5 ? "high" : "medium", `${earlyExits} early exits`);
  push("late_exit", lateLosses, lateLosses > 5 ? "high" : "low", `${lateLosses} late losses`);
  push("revenge_trading", revenge, revenge > 3 ? "high" : "medium", `${revenge} post-loss rushes`);
  push("overtrading", overtradingDays, overtradingDays > 2 ? "high" : "medium", `${overtradingDays} busy days`);
  push("skipping_good_trades", ignored, ignored > 3 ? "medium" : "low", `${ignored} ignored signals`);
  push("chasing_price", chase, chase > 3 ? "high" : "medium", `${chase} chase-like losses`);
  push("fomo", chase, chase > 2 ? "medium" : "low", "Correlated with chase pattern");
  push("holding_losers", lateLosses, lateLosses > 3 ? "medium" : "low", "Overlaps late exit");

  return { flags, generatedAt: Date.now() };
}

export function buildMistakeEvents(
  report: BehaviorReport,
  trades: TradeLearningRecord[],
): MistakeEvent[] {
  const monthAgo = Date.now() - 30 * 86400000;
  const recentMoves = trades
    .filter((t) => t.closedAt >= monthAgo)
    .reduce((s, t) => s + t.stopMoves, 0);

  return report.flags.map((f) => {
    const copy = MISTAKE_COPY[f.flag];
    let description = copy.description(f.count);
    let impact = copy.impact;
    if (f.flag === "moving_stop_loss" && recentMoves > 0) {
      const lossesAfterMove = trades.filter(
        (t) => t.stopMoves > 0 && t.outcome === "loss" && t.closedAt >= monthAgo,
      ).length;
      description = `You moved your stop-loss ${recentMoves} times this month.`;
      impact = `${lossesAfterMove} became larger losses (among moved-stop trades).`;
    }
    return {
      id: uid("mistake"),
      at: Date.now(),
      flag: f.flag,
      description,
      impact,
      recommendation: copy.recommendation,
      evidenceCount: f.count,
    };
  });
}
