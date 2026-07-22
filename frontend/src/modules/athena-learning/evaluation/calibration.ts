import type { CalibrationBucket, TradeLearningRecord } from "../types";
import { confidenceBucket, round } from "../utils/math";

export function calibrateConfidence(trades: TradeLearningRecord[]): CalibrationBucket[] {
  const closed = trades.filter((t) => t.outcome === "win" || t.outcome === "loss");
  const map = new Map<string, { mid: number; wins: number; n: number }>();

  for (const t of closed) {
    const { key, mid } = confidenceBucket(t.confidenceAtEntry);
    const cur = map.get(key) ?? { mid, wins: 0, n: 0 };
    cur.n += 1;
    if (t.outcome === "win") cur.wins += 1;
    map.set(key, cur);
  }

  return [...map.entries()]
    .sort((a, b) => a[1].mid - b[1].mid)
    .map(([bucket, v]) => {
      const actualWinRate = v.n ? round((v.wins / v.n) * 100, 1) : 0;
      const gap = round(v.mid - actualWinRate, 1);
      let bias: CalibrationBucket["bias"] = "calibrated";
      if (gap > 8) bias = "overconfident";
      else if (gap < -8) bias = "underconfident";
      return {
        bucket,
        predictedMid: v.mid,
        sampleSize: v.n,
        actualWinRate,
        bias,
        gap,
      };
    });
}

export function summarizeCalibration(buckets: CalibrationBucket[]): string {
  const over = buckets.filter((b) => b.bias === "overconfident" && b.sampleSize >= 3);
  if (!over.length) return "Confidence appears reasonably calibrated on available samples.";
  const worst = over.sort((a, b) => b.gap - a.gap)[0];
  return `Overconfident in ${worst.bucket}% band: predicted ~${worst.predictedMid}% vs actual ${worst.actualWinRate}% (n=${worst.sampleSize}).`;
}
