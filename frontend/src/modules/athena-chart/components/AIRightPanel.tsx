"use client";

import { useIntelligenceStore } from "../intelligence/store/intelligence-store";
import { useDecisionStore } from "../decision-engine/store/decision-store";
import {
  formatBiasLabel,
  recommendedAction,
} from "../decision-engine/models";
import { cn } from "@/lib/utils";

function Card({
  title,
  children,
  accent,
}: {
  title: string;
  children: React.ReactNode;
  accent?: string;
}) {
  return (
    <div className="rounded-sm border border-border-subtle bg-panel px-3 py-2.5">
      <div
        className={cn(
          "text-[10px] font-medium uppercase tracking-wide text-muted-foreground",
          accent,
        )}
      >
        {title}
      </div>
      <div className="mt-1.5 text-[11px] leading-relaxed text-foreground">{children}</div>
    </div>
  );
}

export function AIRightPanel() {
  const snap = useIntelligenceStore((s) => s.snapshot);
  const analyzing = useIntelligenceStore((s) => s.analyzing);
  const opp = useDecisionStore((s) => s.opportunity);
  const deciding = useDecisionStore((s) => s.deciding);

  if (!snap) {
    return (
      <div className="p-3 text-[11px] text-muted">
        {analyzing ? "Analyzing market structure…" : "Waiting for series…"}
      </div>
    );
  }

  const c = snap.confluence;
  const risk =
    c.overallConfidence > 70
      ? "Elevated — high conviction setup"
      : c.overallConfidence > 45
        ? "Moderate"
        : "Low conviction / choppy";
  const opportunity =
    c.bullishScore > c.bearishScore + 10
      ? `Bullish bias ${Math.round(c.bullishScore)}`
      : c.bearishScore > c.bullishScore + 10
        ? `Bearish bias ${Math.round(c.bearishScore)}`
        : "No clear directional edge";

  const e = opp?.activeEntry;
  const action = recommendedAction(opp);

  return (
    <div className="flex h-full flex-col">
      <div className="space-y-2 overflow-y-auto p-2">
        <Card title="Decision" accent="text-primary">
          {deciding && !opp ? (
            <span className="text-muted">Computing opportunity…</span>
          ) : opp ? (
            <div className="space-y-1">
              <div className="font-mono capitalize">
                {formatBiasLabel(opp.bias)} · Grade {opp.grade}
              </div>
              <div className="text-muted">
                Confidence {Math.round(opp.confidence.score)}% (
                {opp.confidence.label.replace(/_/g, " ")})
              </div>
              <div className="grid grid-cols-3 gap-1 font-mono text-[9px]">
                <span className="text-bullish">
                  B {Math.round(opp.probability.bullish)}%
                </span>
                <span className="text-bearish">
                  S {Math.round(opp.probability.bearish)}%
                </span>
                <span className="text-muted">
                  N {Math.round(opp.probability.neutral)}%
                </span>
              </div>
            </div>
          ) : (
            <span className="text-muted">No decision yet</span>
          )}
        </Card>

        {opp ? (
          <>
            <Card title="Recommended Action">{action}</Card>
            {opp.direction !== "flat" && e ? (
              <Card title="Trade Plan">
                <div className="space-y-0.5 font-mono text-[10px]">
                  <div>Entry {e.entry}</div>
                  <div className="text-bearish">SL {e.stopLoss}</div>
                  <div className="text-bullish">
                    TP1 {e.takeProfit1} · TP2 {e.takeProfit2} · TP3 {e.takeProfit3}
                  </div>
                  <div>
                    RR {e.riskReward} · Risk {opp.risk.category} · Size{" "}
                    {opp.risk.positionSize}
                  </div>
                </div>
              </Card>
            ) : null}
            <Card title="Timeframe Alignment">
              <div className="font-mono text-[10px]">
                Align {opp.mtf.alignmentScore}% · Conflict {opp.mtf.conflictScore}% ·{" "}
                {opp.mtf.dominantBias}
              </div>
              <div className="mt-1 space-y-0.5 font-mono text-[9px] text-muted">
                {opp.mtf.votes.map((v) => (
                  <div key={v.timeframe} className="flex justify-between">
                    <span>{v.timeframe}</span>
                    <span className="capitalize">{v.bias}</span>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="Supporting Signals">
              {opp.supportingSignals.slice(0, 5).map((s) => (
                <div key={s.id} className="font-mono text-[9px] text-bullish">
                  {s.label} · w{Math.round(s.weightedScore)}
                </div>
              ))}
              {!opp.supportingSignals.length ? (
                <span className="text-muted">None</span>
              ) : null}
            </Card>
            <Card title="Conflicting Signals">
              {opp.opposingSignals.slice(0, 4).map((s) => (
                <div key={s.id} className="font-mono text-[9px] text-bearish">
                  {s.label}
                </div>
              ))}
              {!opp.opposingSignals.length ? (
                <span className="text-muted">None</span>
              ) : null}
            </Card>
          </>
        ) : null}

        <Card title="Current Trend" accent="text-primary">
          <div className="font-mono capitalize">
            {snap.trend.classification.replace(/_/g, " ")}
          </div>
          <div className="text-muted">
            Confidence {Math.round(snap.trend.confidence)}% · bias{" "}
            {snap.trend.direction}
          </div>
        </Card>

        <Card title="Market Structure">
          <div className="flex flex-wrap gap-1">
            {snap.structure.slice(-6).map((s) => (
              <span
                key={s.id}
                className={cn(
                  "rounded-sm border px-1 py-0.5 font-mono text-[9px]",
                  s.direction === "bullish"
                    ? "border-bullish/40 text-bullish"
                    : "border-bearish/40 text-bearish",
                )}
              >
                {s.label}
              </span>
            ))}
            {!snap.structure.length ? (
              <span className="text-muted">No structure events</span>
            ) : null}
          </div>
        </Card>

        <Card title="Liquidity">
          {snap.liquidity.slice(0, 4).map((l) => (
            <div key={l.id} className="font-mono text-[10px] text-muted">
              {l.kind.replace(/_/g, " ")} · imp {Math.round(l.importance)}
            </div>
          ))}
          {!snap.liquidity.length ? (
            <span className="text-muted">None detected</span>
          ) : null}
        </Card>

        <Card title="Order Blocks">
          {snap.orderBlocks
            .filter((o) => o.status === "active")
            .slice(0, 3)
            .map((o) => (
              <div key={o.id} className="font-mono text-[10px]">
                <span className={o.bias === "bullish" ? "text-bullish" : "text-bearish"}>
                  {o.bias}
                </span>{" "}
                OB · score {Math.round(o.score)}
                {o.breaker ? " · breaker" : ""}
              </div>
            ))}
          {!snap.orderBlocks.filter((o) => o.status === "active").length ? (
            <span className="text-muted">No active blocks</span>
          ) : null}
        </Card>

        <Card title="FVG">
          {snap.fvgs
            .filter((f) => f.status === "active" || f.status === "partial")
            .slice(0, 3)
            .map((f) => (
              <div key={f.id} className="font-mono text-[10px]">
                {f.bias} · {f.status} · fill {(f.fillRatio * 100).toFixed(0)}%
              </div>
            ))}
        </Card>

        <Card title="Volume">
          <div className="capitalize">
            {snap.volume.participation} participation · {snap.volume.pressure}
          </div>
          <div className="text-muted">
            {[
              snap.volume.absorption && "absorption",
              snap.volume.exhaustion && "exhaustion",
              snap.volume.climax && "climax",
              snap.volume.divergence && "divergence",
            ]
              .filter(Boolean)
              .join(" · ") || "stable"}
          </div>
        </Card>

        <Card title="Confluence Score">
          <div className="font-mono text-sm text-primary">
            {Math.round(c.overallConfidence)}
          </div>
          <div className="mt-1 grid grid-cols-3 gap-1 text-[9px]">
            <span className="text-bullish">B {Math.round(c.bullishScore)}</span>
            <span className="text-bearish">S {Math.round(c.bearishScore)}</span>
            <span className="text-muted">N {Math.round(c.neutralScore)}</span>
          </div>
          <div className="mt-1 text-[9px] text-muted">
            Drivers: {c.drivers.slice(0, 4).map((d) => d.source).join(", ")}
          </div>
        </Card>

        <Card title="Pattern Detection">
          {snap.patterns.slice(0, 4).map((p) => (
            <div key={p.id} className="font-mono text-[10px] capitalize">
              {p.kind.replace(/_/g, " ")} · {Math.round(p.confidence)}%
            </div>
          ))}
          {!snap.patterns.length ? (
            <span className="text-muted">No patterns</span>
          ) : null}
        </Card>

        <Card title="Risk Rating">{risk}</Card>
        <Card title="Opportunity Rating">{opportunity}</Card>

        {snap.mtf ? (
          <Card title="Multi-Timeframe">
            <div className="space-y-0.5 font-mono text-[10px]">
              {snap.mtf.frames.map((f) => (
                <div key={f.timeframe} className="flex justify-between">
                  <span>{f.timeframe}</span>
                  <span className="capitalize">
                    {f.classification.replace(/_/g, " ")}
                  </span>
                </div>
              ))}
              <div className="pt-1 text-muted">
                Agreement {Math.round(snap.mtf.agreementPct)}%
              </div>
            </div>
          </Card>
        ) : null}
      </div>
    </div>
  );
}
