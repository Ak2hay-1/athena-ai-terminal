"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { useAuthStore } from "@/store/auth-store";
import { useLearningStore } from "@/modules/athena-learning/store/learning-store";
import { compareStrategies } from "@/modules/athena-learning/strategies/performance";
import {
  findSimilarSetups,
  patternSuccessRate,
} from "@/modules/athena-learning/models/brain";
import type { StrategyKind } from "@/modules/athena-learning/types";
import { cn } from "@/lib/utils";

export function CoachDashboard() {
  const user = useAuthStore((s) => s.user);
  const userId = user ? String(user.id) : "anonymous";

  const setUserId = useLearningStore((s) => s.setUserId);
  const refresh = useLearningStore((s) => s.refresh);
  const ingestDemo = useLearningStore((s) => s.ingestDemo);
  const analytics = useLearningStore((s) => s.analytics);
  const strategies = useLearningStore((s) => s.strategies);
  const calibration = useLearningStore((s) => s.calibration);
  const bundle = useLearningStore((s) => s.bundle);
  const addGoal = useLearningStore((s) => s.addGoal);
  const activateWeights = useLearningStore((s) => s.activateWeights);
  const rollbackWeights = useLearningStore((s) => s.rollbackWeights);
  const exportData = useLearningStore((s) => s.exportData);
  const deleteData = useLearningStore((s) => s.deleteData);

  const profile = bundle?.profile ?? null;
  const recommendations = bundle?.recommendations ?? [];
  const mistakes = bundle?.mistakes ?? [];
  const achievements = bundle?.achievements ?? [];
  const goals = bundle?.goals ?? [];
  const weights = bundle?.weightHistory ?? [];
  const memory = bundle?.marketMemory ?? [];

  const [labA, setLabA] = useState<StrategyKind>("intraday");
  const [labB, setLabB] = useState<StrategyKind>("swing");
  const [brainTags, setBrainTags] = useState("bullish_bos,order_block");

  useEffect(() => {
    setUserId(userId);
    refresh();
  }, [userId, setUserId, refresh]);

  const stratA = strategies.find((s) => s.strategy === labA);
  const stratB = strategies.find((s) => s.strategy === labB);
  const labRows =
    stratA && stratB ? compareStrategies(stratA, stratB) : [];

  const brainHits = useMemo(() => {
    const tags = brainTags.split(",").map((t) => t.trim()).filter(Boolean);
    return findSimilarSetups(memory, { tags, limit: 20 });
  }, [memory, brainTags]);

  const brainRate = useMemo(() => {
    const tags = brainTags.split(",").map((t) => t.trim()).filter(Boolean);
    return patternSuccessRate(memory, tags);
  }, [memory, brainTags]);

  return (
    <div className="mx-auto max-w-[1400px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Athena Coach
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            Self-learning intelligence
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-muted">
            Explainable improvement from your trades, decisions, and habits —
            not GPT retraining. Learning is isolated to your account.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone="ai">Coach {profile?.coachScore?.toFixed(0) ?? "—"}</Badge>
          <Badge tone="neutral">
            Consistency {profile?.consistencyScore?.toFixed(0) ?? "—"}
          </Badge>
          <Button size="sm" variant="outline" onClick={() => ingestDemo(48)}>
            Load demo history
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              const blob = new Blob([exportData()], { type: "application/json" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `athena-learning-${userId}.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            Export data
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="text-bearish"
            onClick={() => {
              if (confirm("Delete all personal learning data?")) deleteData();
            }}
          >
            Delete learning data
          </Button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Win rate" value={`${analytics?.winRate ?? 0}%`} />
        <MetricCard
          label="Profit factor"
          value={(analytics?.profitFactor ?? 0).toFixed(2)}
        />
        <MetricCard label="Expectancy" value={(analytics?.expectancy ?? 0).toFixed(3)} />
        <MetricCard label="Avg RR" value={(analytics?.avgRr ?? 0).toFixed(2)} />
        <MetricCard label="Drawdown" value={String(analytics?.maxDrawdown ?? 0)} />
        <MetricCard
          label="Decision accuracy"
          value={`${analytics?.decisionAccuracy ?? 0}%`}
        />
        <MetricCard
          label="Confidence accuracy"
          value={`${analytics?.confidenceAccuracy ?? 0}%`}
        />
        <MetricCard label="Trades" value={String(analytics?.tradeCount ?? 0)} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Personal trader profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {profile ? (
              <>
                <Row label="Best session" value={profile.bestSession} />
                <Row label="Weakest session" value={profile.weakestSession} />
                <Row label="Best pair" value={profile.bestPair} />
                <Row label="Best timeframe" value={profile.bestTimeframe} />
                <Row
                  label="Avg hold"
                  value={`${profile.avgHoldMinutes} min`}
                />
                <Row label="Preferred risk" value={profile.preferredRiskMode} />
              </>
            ) : (
              <p className="text-muted">No profile yet — close trades or load demo data.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Learning timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {(analytics?.weeklyTimeline ?? []).slice(-8).map((w) => (
                <div
                  key={w.week}
                  className="flex items-center justify-between font-mono text-xs"
                >
                  <span className="text-muted">{w.week}</span>
                  <span>
                    WR {w.winRate}% · RR {w.avgRr} · n={w.trades}
                  </span>
                </div>
              ))}
              {!analytics?.weeklyTimeline?.length ? (
                <p className="text-sm text-muted">Timeline appears after closed trades.</p>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recommendations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {recommendations.map((r) => (
              <div
                key={r.id}
                className="rounded-md border border-border-subtle bg-panel/40 p-3 text-sm"
              >
                <div className="font-medium">{r.title}</div>
                <p className="mt-1 text-muted">{r.body}</p>
                <p className="mt-2 text-[11px] text-muted-foreground">
                  Why: {r.why}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  Data: {r.basedOn.join(" · ")} · Confidence {r.confidence}%
                  {r.historicalSuccess != null
                    ? ` · Historical ${r.historicalSuccess}%`
                    : ""}
                </p>
              </div>
            ))}
            {!recommendations.length ? (
              <p className="text-sm text-muted">No recommendations yet.</p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Mistakes & habits</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {mistakes.slice(0, 6).map((m) => (
              <div key={m.id} className="border-b border-border-subtle pb-2 text-sm">
                <div className="font-medium capitalize">
                  {m.flag.replace(/_/g, " ")}
                </div>
                <p className="text-muted">{m.description}</p>
                <p className="text-[11px] text-bearish">{m.impact}</p>
                <p className="text-[11px] text-primary">{m.recommendation}</p>
              </div>
            ))}
            {!mistakes.length ? (
              <p className="text-sm text-muted">No behavior flags yet.</p>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Goals</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => addGoal("Reach 65% win rate", "win_rate", 65, "%")}
              >
                + Win rate 65%
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => addGoal("Minimum RR 2", "min_rr", 2, "R")}
              >
                + Min RR 2
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() =>
                  addGoal("Max 4 trades / day", "max_daily_trades", 4, "trades")
                }
              >
                + Max 4 daily
              </Button>
            </div>
            {goals.map((g) => (
              <div key={g.id} className="text-sm">
                <div className="flex justify-between">
                  <span>{g.title}</span>
                  <span className="font-mono text-xs">
                    {g.current}
                    {g.unit} / {g.target}
                    {g.unit}
                  </span>
                </div>
                <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-border">
                  <div
                    className={cn(
                      "h-full bg-primary",
                      g.achievedAt && "bg-bullish",
                    )}
                    style={{
                      width: `${Math.min(100, (g.current / g.target) * 100)}%`,
                    }}
                  />
                </div>
              </div>
            ))}
            {!goals.length ? (
              <p className="text-sm text-muted">Add a goal to start tracking.</p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Achievements</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 sm:grid-cols-2">
            {achievements.map((a) => (
              <div
                key={a.id}
                className={cn(
                  "rounded-md border p-2 text-xs",
                  a.unlockedAt
                    ? "border-primary/40 bg-primary/10"
                    : "border-border-subtle text-muted",
                )}
              >
                <div className="font-medium text-foreground">{a.title}</div>
                <div>{a.description}</div>
                <div className="mt-1 font-mono">
                  {a.progress}/{a.target}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Confidence calibration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-muted">
                <tr>
                  <th className="py-1">Bucket</th>
                  <th>Predicted</th>
                  <th>Actual</th>
                  <th>Gap</th>
                  <th>Bias</th>
                  <th>n</th>
                </tr>
              </thead>
              <tbody>
                {calibration.map((c) => (
                  <tr key={c.bucket} className="border-t border-border-subtle font-mono">
                    <td className="py-1">{c.bucket}</td>
                    <td>{c.predictedMid}%</td>
                    <td>{c.actualWinRate}%</td>
                    <td>{c.gap}</td>
                    <td
                      className={
                        c.bias === "overconfident"
                          ? "text-bearish"
                          : c.bias === "underconfident"
                            ? "text-warning"
                            : ""
                      }
                    >
                      {c.bias}
                    </td>
                    <td>{c.sampleSize}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!calibration.length ? (
              <p className="text-sm text-muted">Need closed trades for calibration.</p>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Strategy laboratory</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2 text-sm">
            <label>
              A{" "}
              <select
                value={labA}
                onChange={(e) => setLabA(e.target.value as StrategyKind)}
                className="rounded border border-border bg-panel px-1"
              >
                {strategies.map((s) => (
                  <option key={s.strategy} value={s.strategy}>
                    {s.strategy}
                  </option>
                ))}
              </select>
            </label>
            <label>
              B{" "}
              <select
                value={labB}
                onChange={(e) => setLabB(e.target.value as StrategyKind)}
                className="rounded border border-border bg-panel px-1"
              >
                {strategies.map((s) => (
                  <option key={s.strategy} value={s.strategy}>
                    {s.strategy}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <table className="w-full text-left text-xs">
            <thead className="text-muted">
              <tr>
                <th className="py-1">Metric</th>
                <th>A</th>
                <th>B</th>
                <th>Edge</th>
              </tr>
            </thead>
            <tbody>
              {labRows.map((r) => (
                <tr key={r.metric} className="border-t border-border-subtle font-mono">
                  <td className="py-1">{r.metric}</td>
                  <td>{r.a}</td>
                  <td>{r.b}</td>
                  <td>{r.winner}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Adaptive weights</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p className="text-muted">
            Proposed changes require evidence and stay inactive until you approve.
            Rollback is always available.
          </p>
          {weights.slice(-5).reverse().map((w) => (
            <div
              key={w.version}
              className="flex flex-wrap items-center justify-between gap-2 rounded border border-border-subtle p-2"
            >
              <div>
                <div className="font-mono text-xs">
                  {w.version} {w.active ? "(active)" : ""}
                </div>
                <div className="text-[11px] text-muted">{w.reason}</div>
                <div className="text-[10px] text-muted-foreground">
                  {w.evidence.slice(0, 2).join(" · ")}
                </div>
              </div>
              {!w.active ? (
                <Button size="sm" variant="outline" onClick={() => activateWeights(w.version)}>
                  Activate
                </Button>
              ) : null}
            </div>
          ))}
          <Button size="sm" variant="outline" onClick={() => rollbackWeights()}>
            Rollback weights
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Athena Brain — similar setups</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted">
            Proprietary historical memory (your events only). Ask: how often did
            similar confluences succeed?
          </p>
          <input
            value={brainTags}
            onChange={(e) => setBrainTags(e.target.value)}
            className="w-full rounded border border-border bg-panel px-2 py-1 text-sm"
            placeholder="tags: bullish_bos,order_block,liquidity_sweep"
          />
          <div className="text-sm">
            Success rate:{" "}
            <span className="font-mono text-primary">
              {brainRate.rate}% (n={brainRate.sample})
            </span>
          </div>
          <div className="max-h-48 space-y-1 overflow-y-auto text-xs">
            {brainHits.map((h) => (
              <div
                key={h.event.id}
                className="flex justify-between border-b border-border-subtle py-1 font-mono"
              >
                <span>
                  {h.event.symbol} {h.event.timeframe} · {h.event.tags.slice(0, 3).join(",")}
                </span>
                <span>
                  {h.similarity}% · {h.event.outcome}
                </span>
              </div>
            ))}
            {!brainHits.length ? (
              <p className="text-muted">No similar events in personal market memory yet.</p>
            ) : null}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted">{label}</span>
      <span className="font-medium capitalize">{value}</span>
    </div>
  );
}
