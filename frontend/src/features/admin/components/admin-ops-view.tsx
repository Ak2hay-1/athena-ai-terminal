"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  cleanupMarketCandles,
  getAdminSchedulers,
  syncNewsFeeds,
  triggerMarketCollection,
  triggerSchedulerJob,
} from "@/services/admin";
import { ApiError } from "@/services/api-client";
import type { SchedulerJobStatus, SchedulerStatus } from "@/types";

function formatNextRun(value?: string | null) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function defaultCleanupDate() {
  const date = new Date();
  date.setDate(date.getDate() - 30);
  return date.toISOString().slice(0, 16);
}

export function AdminOpsView() {
  const queryClient = useQueryClient();
  const [cleanupBefore, setCleanupBefore] = useState(defaultCleanupDate);
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  const schedulersQuery = useQuery({
    queryKey: ["admin", "schedulers"],
    queryFn: getAdminSchedulers,
    refetchInterval: 15_000,
  });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["admin", "schedulers"] });
  };

  const triggerJobMutation = useMutation({
    mutationFn: (jobId: string) => triggerSchedulerJob(jobId),
    onSuccess: (result) => {
      setLastMessage(`Triggered ${result.triggered}`);
      invalidate();
    },
  });

  const marketRunMutation = useMutation({
    mutationFn: (timeframe: string) => triggerMarketCollection(timeframe),
    onSuccess: (result) => {
      setLastMessage(`Market collection queued for ${result.timeframe}`);
      invalidate();
    },
  });

  const newsSyncMutation = useMutation({
    mutationFn: syncNewsFeeds,
    onSuccess: (result) => {
      setLastMessage(`News sync inserted ${result.inserted} events`);
    },
  });

  const cleanupMutation = useMutation({
    mutationFn: () => cleanupMarketCandles(new Date(cleanupBefore).toISOString()),
    onSuccess: (result) => {
      setLastMessage(`Deleted ${result.deleted} candles before ${result.before}`);
    },
  });

  const schedulers = schedulersQuery.data;
  const pending =
    triggerJobMutation.isPending ||
    marketRunMutation.isPending ||
    newsSyncMutation.isPending ||
    cleanupMutation.isPending;

  const error =
    schedulersQuery.error ||
    triggerJobMutation.error ||
    marketRunMutation.error ||
    newsSyncMutation.error ||
    cleanupMutation.error;

  const errorMessage =
    error instanceof ApiError
      ? error.message
      : error instanceof Error
        ? error.message
        : null;

  const marketTimeframes =
    schedulers?.market.jobs
      .map((job) => job.id.replace(/^collect_/, "").toUpperCase())
      .filter(Boolean) ?? [];

  return (
    <div className="mx-auto max-w-[1200px] space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Administration
          </p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight">Ops controls</h2>
          <p className="mt-1 text-sm text-muted">
            Schedulers, news sync, and market data maintenance.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => void schedulersQuery.refetch()}
          disabled={schedulersQuery.isFetching}
        >
          <RefreshCw className={`h-3.5 w-3.5 ${schedulersQuery.isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {errorMessage ? (
        <div className="rounded-sm border border-bearish/30 bg-bearish/10 px-4 py-3 text-sm text-bearish">
          {errorMessage}
        </div>
      ) : null}

      {lastMessage ? (
        <div className="rounded-sm border border-bullish/30 bg-bullish/10 px-4 py-3 text-sm text-bullish">
          {lastMessage}
        </div>
      ) : null}

      {schedulers ? (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <SchedulerCard
              title="Market collector"
              description={`Timezone ${schedulers.timezone}`}
              status={schedulers.market}
              pending={pending}
              onRunJob={(jobId) => triggerJobMutation.mutate(jobId)}
            />
            <SchedulerCard
              title="News & learning"
              description="RSS sync, outcome labeling, model retrain"
              status={schedulers.news_learning}
              pending={pending}
              onRunJob={(jobId) => triggerJobMutation.mutate(jobId)}
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Market collection</CardTitle>
                <CardDescription>Queue an immediate collect+analyze pass</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {marketTimeframes.length === 0 ? (
                  <p className="text-sm text-muted">No market jobs registered.</p>
                ) : (
                  marketTimeframes.map((tf) => (
                    <Button
                      key={tf}
                      size="sm"
                      variant="secondary"
                      disabled={pending}
                      onClick={() => marketRunMutation.mutate(tf)}
                    >
                      Run {tf}
                    </Button>
                  ))
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>News sync</CardTitle>
                <CardDescription>Pull RSS feeds into news_events now</CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  size="sm"
                  variant="ai"
                  disabled={pending}
                  onClick={() => newsSyncMutation.mutate()}
                >
                  {newsSyncMutation.isPending ? "Syncing…" : "Sync news feeds"}
                </Button>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Market cleanup</CardTitle>
              <CardDescription>
                Permanently delete candles older than the selected timestamp
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-end gap-3">
              <label className="space-y-1 text-sm">
                <span className="text-muted-foreground">Delete before</span>
                <input
                  type="datetime-local"
                  value={cleanupBefore}
                  onChange={(event) => setCleanupBefore(event.target.value)}
                  className="block h-9 rounded-sm border border-border bg-panel px-3 text-sm outline-none focus:border-primary/50"
                />
              </label>
              <Button
                size="sm"
                variant="danger"
                disabled={pending || !cleanupBefore}
                onClick={() => {
                  if (
                    window.confirm(
                      "Delete all candles before this timestamp? This cannot be undone.",
                    )
                  ) {
                    cleanupMutation.mutate();
                  }
                }}
              >
                {cleanupMutation.isPending ? "Deleting…" : "Delete candles"}
              </Button>
            </CardContent>
          </Card>
        </>
      ) : schedulersQuery.isLoading ? (
        <p className="text-sm text-muted">Loading schedulers…</p>
      ) : null}
    </div>
  );
}

function SchedulerCard({
  title,
  description,
  status,
  pending,
  onRunJob,
}: {
  title: string;
  description: string;
  status: SchedulerStatus;
  pending: boolean;
  onRunJob: (jobId: string) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <Badge tone={status.running ? "bullish" : "bearish"}>
            {status.running ? "Running" : "Stopped"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {status.jobs.length === 0 ? (
          <p className="text-sm text-muted">No jobs registered.</p>
        ) : (
          status.jobs.map((job) => (
            <JobRow
              key={job.id}
              job={job}
              pending={pending}
              onRun={() => onRunJob(job.id)}
            />
          ))
        )}
      </CardContent>
    </Card>
  );
}

function JobRow({
  job,
  pending,
  onRun,
}: {
  job: SchedulerJobStatus;
  pending: boolean;
  onRun: () => void;
}) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-sm border border-border/70 px-3 py-2.5">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{job.id}</p>
        <p className="mt-0.5 text-xs text-muted">{job.trigger}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Next: {formatNextRun(job.next_run_time)}
        </p>
      </div>
      <Button size="sm" variant="secondary" disabled={pending} onClick={onRun}>
        Run now
      </Button>
    </div>
  );
}
