"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import {
  getAdminOverview,
  getLearningStats,
  initializeMt5,
  labelLearningOutcomes,
  retrainLearning,
  shutdownMt5,
} from "@/services/admin";
import { ApiError } from "@/services/api-client";

function toneForStatus(ok: boolean): "bullish" | "bearish" | "warning" {
  return ok ? "bullish" : "bearish";
}

export function AdminOverviewView() {
  const queryClient = useQueryClient();

  const overviewQuery = useQuery({
    queryKey: ["admin", "overview"],
    queryFn: getAdminOverview,
    refetchInterval: 30_000,
  });

  const learningStatsQuery = useQuery({
    queryKey: ["admin", "learning-stats"],
    queryFn: () => getLearningStats("XAUUSD", "M1"),
  });

  const retrainMutation = useMutation({
    mutationFn: retrainLearning,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin"] });
    },
  });

  const labelMutation = useMutation({
    mutationFn: labelLearningOutcomes,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin"] });
    },
  });

  const mt5InitMutation = useMutation({
    mutationFn: initializeMt5,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "overview"] });
    },
  });

  const mt5ShutdownMutation = useMutation({
    mutationFn: shutdownMt5,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "overview"] });
    },
  });

  const overview = overviewQuery.data;
  const errorMessage =
    overviewQuery.error instanceof ApiError
      ? overviewQuery.error.message
      : overviewQuery.error
        ? "Failed to load admin overview"
        : null;

  return (
    <div className="mx-auto max-w-[1200px] space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Administration
          </p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight">Ops overview</h2>
          <p className="mt-1 text-sm text-muted">
            Platform health, MT5, learning controls, and runtime config.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => void overviewQuery.refetch()}
          disabled={overviewQuery.isFetching}
        >
          <RefreshCw className={`h-3.5 w-3.5 ${overviewQuery.isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {errorMessage ? (
        <div className="rounded-sm border border-bearish/30 bg-bearish/10 px-4 py-3 text-sm text-bearish">
          {errorMessage}
        </div>
      ) : null}

      {overview ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="API health"
              value={overview.health.status}
              hint={`DB ${overview.health.database}`}
              tone={toneForStatus(overview.health.status === "healthy")}
            />
            <MetricCard
              label="Users"
              value={String(overview.users.total)}
              hint={`${overview.users.active} active · ${overview.users.admins} admin`}
              tone="primary"
            />
            <MetricCard
              label="MT5"
              value={overview.mt5.connected ? "Connected" : "Offline"}
              hint={overview.mt5.message}
              tone={toneForStatus(overview.mt5.connected)}
            />
            <MetricCard
              label="Learning"
              value={overview.learning.enabled ? "Enabled" : "Off"}
              hint={`Retrain every ${overview.learning.retrain_interval_hours}h`}
              tone={overview.learning.enabled ? "ai" : "warning"}
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>MetaTrader 5</CardTitle>
                <CardDescription>Terminal connection and account status</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Badge tone={overview.mt5.connected ? "bullish" : "bearish"}>
                    {overview.mt5.connected ? "Connected" : "Disconnected"}
                  </Badge>
                  <Badge tone={overview.mt5.initialized ? "primary" : "neutral"}>
                    {overview.mt5.initialized ? "Initialized" : "Not initialized"}
                  </Badge>
                  <Badge tone={overview.mt5.logged_in ? "bullish" : "warning"}>
                    {overview.mt5.logged_in ? "Logged in" : "Not logged in"}
                  </Badge>
                </div>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <dt className="text-muted-foreground">Server</dt>
                    <dd className="mt-0.5 font-medium">{overview.mt5.server || "—"}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Login</dt>
                    <dd className="mt-0.5 font-medium">{overview.mt5.login ?? "—"}</dd>
                  </div>
                </dl>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={mt5InitMutation.isPending}
                    onClick={() => mt5InitMutation.mutate()}
                  >
                    Initialize
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    disabled={mt5ShutdownMutation.isPending}
                    onClick={() => mt5ShutdownMutation.mutate()}
                  >
                    Shutdown
                  </Button>
                </div>
                {(mt5InitMutation.error || mt5ShutdownMutation.error) && (
                  <p className="text-xs text-bearish">
                    {mt5InitMutation.error instanceof Error
                      ? mt5InitMutation.error.message
                      : mt5ShutdownMutation.error instanceof Error
                        ? mt5ShutdownMutation.error.message
                        : "MT5 action failed"}
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Learning pipeline</CardTitle>
                <CardDescription>Outcome labeling and model retraining</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <dt className="text-muted-foreground">Min samples</dt>
                    <dd className="mt-0.5 font-medium">{overview.learning.min_samples}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Model path</dt>
                    <dd className="mt-0.5 truncate font-medium">{overview.learning.model_path}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">XAUUSD M1 samples</dt>
                    <dd className="mt-0.5 font-medium">
                      {String(learningStatsQuery.data?.sample_size ?? "—")}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Model accuracy</dt>
                    <dd className="mt-0.5 font-medium">
                      {learningStatsQuery.data?.model_accuracy != null
                        ? `${Number(learningStatsQuery.data.model_accuracy).toFixed(1)}%`
                        : "—"}
                    </dd>
                  </div>
                </dl>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="ai"
                    disabled={labelMutation.isPending || !overview.learning.enabled}
                    onClick={() => labelMutation.mutate()}
                  >
                    {labelMutation.isPending ? "Labeling…" : "Label outcomes"}
                  </Button>
                  <Button
                    size="sm"
                    disabled={retrainMutation.isPending || !overview.learning.enabled}
                    onClick={() => retrainMutation.mutate()}
                  >
                    {retrainMutation.isPending ? "Retraining…" : "Retrain models"}
                  </Button>
                </div>
                {labelMutation.data ? (
                  <p className="text-xs text-muted">Labeled {labelMutation.data.labeled} outcomes.</p>
                ) : null}
                {retrainMutation.data ? (
                  <p className="text-xs text-muted">
                    Retrained {retrainMutation.data.length} symbol/timeframe models.
                  </p>
                ) : null}
                {(labelMutation.error || retrainMutation.error) && (
                  <p className="text-xs text-bearish">
                    {labelMutation.error instanceof Error
                      ? labelMutation.error.message
                      : retrainMutation.error instanceof Error
                        ? retrainMutation.error.message
                        : "Learning action failed"}
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Runtime config</CardTitle>
              <CardDescription>Read-only values from environment settings</CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 text-sm">
                <div>
                  <dt className="text-muted-foreground">Environment</dt>
                  <dd className="mt-0.5 font-medium">{overview.config.app_env}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Execution</dt>
                  <dd className="mt-0.5 font-medium">{overview.config.execution_provider}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">AI provider</dt>
                  <dd className="mt-0.5 font-medium">{overview.config.ai_provider}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">AI model</dt>
                  <dd className="mt-0.5 font-medium">{overview.config.ai_model}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Collector interval</dt>
                  <dd className="mt-0.5 font-medium">
                    {overview.config.collector_interval_seconds}s
                  </dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-muted-foreground">Symbols</dt>
                  <dd className="mt-1 flex flex-wrap gap-1.5">
                    {overview.config.market_symbols.map((symbol) => (
                      <Badge key={symbol} tone="neutral">
                        {symbol}
                      </Badge>
                    ))}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Timeframes</dt>
                  <dd className="mt-1 flex flex-wrap gap-1.5">
                    {overview.config.market_timeframes.map((tf) => (
                      <Badge key={tf} tone="primary">
                        {tf}
                      </Badge>
                    ))}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </>
      ) : overviewQuery.isLoading ? (
        <p className="text-sm text-muted">Loading overview…</p>
      ) : null}
    </div>
  );
}
