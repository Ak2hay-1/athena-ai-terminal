"use client";

import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { MetricCard } from "@/components/ui/metric-card";
import { ConfidenceCalibration } from "@/features/learning/components/confidence-calibration";
import { FeatureAnalytics } from "@/features/learning/components/feature-analytics";
import { MarketRegimeAnalytics } from "@/features/learning/components/market-regime-analytics";
import { SymbolPerformance } from "@/features/learning/components/symbol-performance";
import { TimeframePerformance } from "@/features/learning/components/timeframe-performance";
import { WeightEvolution } from "@/features/learning/components/weight-evolution";
import {
  getLearningDashboard,
  getLearningWeights,
} from "@/services/learning";
import { useAuthStore } from "@/store/auth-store";

export function LearningDashboard() {
  const user = useAuthStore((s) => s.user);

  const dashboardQuery = useQuery({
    queryKey: ["learning", "dashboard"],
    queryFn: getLearningDashboard,
    enabled: Boolean(user),
    refetchInterval: 120_000,
  });

  const weightsQuery = useQuery({
    queryKey: ["learning", "weights"],
    queryFn: () => getLearningWeights(),
    enabled: Boolean(user),
    refetchInterval: 120_000,
  });

  const data = dashboardQuery.data;
  const weights = weightsQuery.data;

  if (dashboardQuery.isLoading) {
    return (
      <div className="mx-auto max-w-[1400px] py-16 text-center text-sm text-muted">
        Loading continuous learning…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1400px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Continuous learning
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            Deterministic performance loop
          </h1>
          <p className="mt-1 text-sm text-muted">
            Outcomes, calibration, and versioned confidence weights — no LLM.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone="ai">Learning {data?.learning_version ?? "—"}</Badge>
          <Badge tone="neutral">Weights {data?.weight_version ?? "baseline"}</Badge>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Win rate"
          value={`${(data?.win_rate ?? 0).toFixed(1)}%`}
        />
        <MetricCard
          label="Profit factor"
          value={(data?.profit_factor ?? 0).toFixed(2)}
        />
        <MetricCard label="Samples" value={String(data?.sample_size ?? 0)} />
        <MetricCard
          label="Wins / Losses"
          value={`${data?.wins ?? 0} / ${data?.losses ?? 0}`}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <ConfidenceCalibration items={data?.calibration ?? []} />
        <WeightEvolution
          active={weights?.active ?? data?.weights ?? {}}
          version={weights?.version ?? data?.weight_version ?? "baseline"}
          history={weights?.history ?? []}
        />
      </div>

      <FeatureAnalytics items={data?.features ?? []} />

      <div className="grid gap-4 xl:grid-cols-2">
        <SymbolPerformance items={data?.symbols ?? []} />
        <TimeframePerformance items={data?.timeframes ?? []} />
      </div>

      <MarketRegimeAnalytics items={data?.regimes ?? []} />
    </div>
  );
}
