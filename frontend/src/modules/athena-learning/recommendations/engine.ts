import type {
  ExplainableRecommendation,
  StrategyPerformance,
  TraderProfile,
  BehaviorReport,
  CalibrationBucket,
} from "../types";
import { uid } from "../utils/math";

/** Personalized, data-backed recommendations — never generic. */
export function generateRecommendations(input: {
  profile: TraderProfile | null;
  strategies: StrategyPerformance[];
  behaviors: BehaviorReport;
  calibration: CalibrationBucket[];
}): ExplainableRecommendation[] {
  const out: ExplainableRecommendation[] = [];
  const { profile, strategies, behaviors, calibration } = input;
  if (!profile || profile.totalTrades < 3) {
    out.push({
      id: uid("rec"),
      createdAt: Date.now(),
      title: "Build your sample",
      body: "Complete at least 10 evaluated trades so Athena can personalize coaching.",
      why: "Recommendations require statistically meaningful per-user history.",
      basedOn: ["trade_count"],
      confidence: 40,
      category: "strategy",
    });
    return out;
  }

  if (profile.weakestSession && profile.weakestSession !== "—") {
    const wr = profile.sessionStats[profile.weakestSession]?.winRate ?? 0;
    const bestWr = profile.sessionStats[profile.bestSession]?.winRate ?? 0;
    const delta = Math.round(bestWr - wr);
    if (delta >= 10) {
      out.push({
        id: uid("rec"),
        createdAt: Date.now(),
        title: `Avoid trading in ${profile.weakestSession}`,
        body: `You perform about ${delta}% worse in ${profile.weakestSession} vs ${profile.bestSession}.`,
        why: "Session win-rate gap exceeds 10 percentage points on your own trades.",
        basedOn: [
          `session:${profile.weakestSession}=${wr}%`,
          `session:${profile.bestSession}=${bestWr}%`,
          `n=${profile.totalTrades}`,
        ],
        confidence: Math.min(92, 55 + delta),
        historicalSuccess: wr,
        expectedImprovement: `Focus on ${profile.bestSession} to lift expectancy`,
        category: "session",
      });
    }
  }

  if (profile.bestSession && profile.bestSession !== "—") {
    out.push({
      id: uid("rec"),
      createdAt: Date.now(),
      title: `Your best trades occur around ${profile.bestSession}`,
      body: `Prioritize setups during ${profile.bestSession} when Decision Engine grade is B+ or higher.`,
      why: "Highest session win rate in your personal profile.",
      basedOn: [`best_session=${profile.bestSession}`, `win_rate=${profile.winRate}%`],
      confidence: 70,
      historicalSuccess: profile.sessionStats[profile.bestSession]?.winRate,
      category: "session",
    });
  }

  if (profile.bestPair && profile.avgRr < 1.8) {
    out.push({
      id: uid("rec"),
      createdAt: Date.now(),
      title: `Increase RR target on ${profile.bestPair}`,
      body: `Your average RR is ${profile.avgRr}. On ${profile.bestPair}, aim for ≥2R when liquidity confirms.`,
      why: "Pair shows relative strength but realized RR trails a 2.0 target.",
      basedOn: [`pair=${profile.bestPair}`, `avg_rr=${profile.avgRr}`],
      confidence: 65,
      expectedImprovement: "Higher RR on strongest pair",
      category: "rr",
    });
  }

  const over = calibration.find((c) => c.bias === "overconfident" && c.sampleSize >= 3);
  if (over) {
    out.push({
      id: uid("rec"),
      createdAt: Date.now(),
      title: "Tighten confidence threshold",
      body: `In the ${over.bucket}% confidence band you are overconfident (predicted ${over.predictedMid}% vs actual ${over.actualWinRate}%).`,
      why: "Calibration gap > 8pts with sufficient samples.",
      basedOn: [
        `bucket=${over.bucket}`,
        `gap=${over.gap}`,
        `n=${over.sampleSize}`,
      ],
      confidence: 80,
      historicalSuccess: over.actualWinRate,
      category: "risk",
    });
  }

  const bestStrat = [...strategies]
    .filter((s) => s.trades >= 3)
    .sort((a, b) => b.expectancy - a.expectancy)[0];
  const current = strategies.find((s) => s.strategy === "intraday");
  if (bestStrat && current && bestStrat.strategy !== "intraday" && bestStrat.expectancy > current.expectancy) {
    const lift = Math.round(
      ((bestStrat.expectancy - current.expectancy) / Math.abs(current.expectancy || 0.01)) * 100,
    );
    out.push({
      id: uid("rec"),
      createdAt: Date.now(),
      title: `Consider ${bestStrat.strategy} profile`,
      body: `Your statistics show ${bestStrat.strategy} mode increases expectancy by ~${Math.abs(lift)}% vs intraday baseline.`,
      why: "Strategy laboratory expectancy comparison on your closed trades.",
      basedOn: [
        `${bestStrat.strategy}_exp=${bestStrat.expectancy}`,
        `intraday_exp=${current.expectancy}`,
        `n=${bestStrat.trades}`,
      ],
      confidence: 72,
      expectedImprovement: `${bestStrat.strategy} expectancy edge`,
      category: "strategy",
    });
  }

  for (const f of behaviors.flags.filter((x) => x.severity !== "low").slice(0, 3)) {
    out.push({
      id: uid("rec"),
      createdAt: Date.now(),
      title: `Address ${f.flag.replace(/_/g, " ")}`,
      body: f.evidence,
      why: "Behavior engine flagged a recurring pattern in your trade log.",
      basedOn: [`behavior=${f.flag}`, `count=${f.count}`, `severity=${f.severity}`],
      confidence: f.severity === "high" ? 85 : 70,
      category: "behavior",
    });
  }

  return out.slice(0, 10);
}
