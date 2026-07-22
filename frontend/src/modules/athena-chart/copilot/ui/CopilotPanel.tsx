"use client";

import { useEffect, useState } from "react";
import type { Candlestick } from "../../types";
import { useCopilotStore } from "../store/copilot-store";
import { useCopilot } from "../services/useCopilot";
import { useTradeCloseReview } from "../services/useTradeCloseReview";
import type { CopilotTab, QuickActionId, SummaryHorizon } from "../types";
import { QUICK_ACTION_LABELS } from "../utils/suggestions";
import { cn } from "@/lib/utils";

const TABS: Array<{ id: CopilotTab; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "analysis", label: "Analysis" },
  { id: "chat", label: "Chat" },
  { id: "trade", label: "Trade" },
  { id: "journal", label: "Journal" },
  { id: "coach", label: "Coach" },
  { id: "history", label: "History" },
];

const QUICK: QuickActionId[] = [
  "explain_chart",
  "explain_trend",
  "explain_structure",
  "why_buy",
  "why_sell",
  "current_risks",
  "find_better_entry",
  "review_my_trade",
  "summarize_session",
  "detect_mistakes",
  "generate_journal",
];

const SUMMARIES: SummaryHorizon[] = ["1m", "5m", "1h", "session", "daily", "weekly"];

export function CopilotPanel({ candles }: { candles: Candlestick[] }) {
  const tab = useCopilotStore((s) => s.tab);
  const setTab = useCopilotStore((s) => s.setTab);
  const messages = useCopilotStore((s) => s.messages);
  const busy = useCopilotStore((s) => s.busy);
  const lastError = useCopilotStore((s) => s.lastError);
  const journalDraft = useCopilotStore((s) => s.journalDraft);
  const lastInsights = useCopilotStore((s) => s.lastInsights);
  const settings = useCopilotStore((s) => s.settings);
  const setSettings = useCopilotStore((s) => s.setSettings);
  const togglePin = useCopilotStore((s) => s.togglePin);
  const pinnedIds = useCopilotStore((s) => s.pinnedIds);
  const threads = useCopilotStore((s) => s.threads);
  const selectedObject = useCopilotStore((s) => s.selectedObject);

  const {
    ctx,
    suggestions,
    ask,
    runQuick,
    summarize,
    coach,
    review,
    ensureThread,
  } = useCopilot(candles);

  useTradeCloseReview(candles.length);

  const [draft, setDraft] = useState("");

  useEffect(() => {
    ensureThread();
  }, [ensureThread]);

  const o = ctx.opportunity;

  return (
    <div className="flex h-full flex-col bg-[#0a0a0a]">
      <div className="flex items-center justify-between border-b border-border px-2 py-1.5">
        <div className="text-[10px] font-medium uppercase tracking-wide text-primary">
          Athena Copilot
        </div>
        <select
          value={settings.provider}
          onChange={(e) =>
            setSettings({
              provider: e.target.value as typeof settings.provider,
            })
          }
          className="rounded-sm border border-border bg-panel px-1 text-[9px] text-muted"
          title="AI Provider"
        >
          <option value="azure">Azure</option>
          <option value="openai">OpenAI</option>
          <option value="mock">Mock</option>
          <option value="local">Local</option>
        </select>
      </div>

      <div className="flex gap-0.5 overflow-x-auto border-b border-border-subtle px-1 py-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              "shrink-0 rounded-sm px-1.5 py-0.5 text-[9px] uppercase tracking-wide",
              tab === t.id
                ? "bg-primary/15 text-primary"
                : "text-muted hover:text-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {tab === "overview" ? (
          <div className="space-y-2 text-[11px]">
            <Block title="Trade Summary">
              {o ? (
                <div className="space-y-0.5 font-mono text-[10px]">
                  <div className="capitalize">
                    {o.bias.replace(/_/g, " ")} · Grade {o.grade}
                  </div>
                  <div>
                    Confidence {o.confidence}% ·{" "}
                    {o.probability.bullish}% / {o.probability.bearish}% /{" "}
                    {o.probability.neutral}%
                  </div>
                  {o.entry != null ? (
                    <div>
                      Entry {o.entry} · SL {o.stopLoss} · TP {o.takeProfit1}
                    </div>
                  ) : (
                    <div className="text-muted">Flat — no active entry</div>
                  )}
                </div>
              ) : (
                <span className="text-muted">Waiting for Decision Engine…</span>
              )}
            </Block>
            <Block title="AI Insights">
              <div className="whitespace-pre-wrap text-[10px] text-muted">
                {lastInsights?.slice(0, 600) ||
                  "Run a quick action or ask a question to generate insights."}
              </div>
            </Block>
            <Block title="Suggested">
              <div className="flex flex-wrap gap-1">
                {suggestions.map((q) => (
                  <button
                    key={q}
                    type="button"
                    disabled={busy}
                    onClick={() => {
                      setTab("chat");
                      void ask(q);
                    }}
                    className="rounded-sm border border-border px-1.5 py-0.5 text-[9px] text-muted hover:border-primary/40 hover:text-primary"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </Block>
            {ctx.dataGaps.length ? (
              <Block title="Data Gaps">
                <span className="text-[10px] text-amber-500">
                  {ctx.dataGaps.join(", ")}
                </span>
              </Block>
            ) : null}
          </div>
        ) : null}

        {tab === "analysis" ? (
          <div className="space-y-2 text-[11px]">
            <Block title="Context">
              <div className="font-mono text-[10px] text-muted">
                {ctx.symbol} · {ctx.timeframe}
                <br />
                Trend {ctx.trend.classification} ({Math.round(ctx.trend.confidence)}
                %)
                <br />
                Structure {ctx.structure.latestLabels.slice(-4).join(", ") || "—"}
                <br />
                Confluence {ctx.confluence.confidence}
              </div>
            </Block>
            <Block title="Market Summaries">
              <div className="flex flex-wrap gap-1">
                {SUMMARIES.map((h) => (
                  <button
                    key={h}
                    type="button"
                    disabled={busy}
                    onClick={() => void summarize(h)}
                    className="rounded-sm border border-border px-1.5 py-0.5 text-[9px] hover:border-primary/40"
                  >
                    {h}
                  </button>
                ))}
              </div>
            </Block>
            <Block title="Reasoning (Decision Engine)">
              <ul className="list-inside list-disc text-[10px] text-muted">
                {(o?.explanationReasons ?? []).slice(0, 6).map((r) => (
                  <li key={r}>{r}</li>
                ))}
                {!o?.explanationReasons?.length ? (
                  <li>No decision reasons yet</li>
                ) : null}
              </ul>
            </Block>
          </div>
        ) : null}

        {tab === "chat" ? (
          <div className="flex h-full min-h-[280px] flex-col">
            <div className="mb-2 flex flex-wrap gap-1">
              {QUICK.slice(0, 6).map((id) => (
                <button
                  key={id}
                  type="button"
                  disabled={busy}
                  onClick={() => void runQuick(id)}
                  className="rounded-sm border border-border px-1.5 py-0.5 text-[9px] text-muted hover:text-primary"
                >
                  {QUICK_ACTION_LABELS[id]}
                </button>
              ))}
            </div>
            {selectedObject ? (
              <div className="mb-2 text-[9px] text-primary">
                Focus: {selectedObject.kind} — {selectedObject.label}
              </div>
            ) : null}
            <div className="min-h-0 flex-1 space-y-2 overflow-y-auto">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={cn(
                    "rounded-sm border px-2 py-1.5 text-[10px]",
                    m.role === "user"
                      ? "border-border-subtle bg-panel text-foreground"
                      : "border-primary/20 bg-primary/5 text-foreground",
                    m.pinned && "ring-1 ring-primary/40",
                  )}
                >
                  <div className="mb-0.5 flex items-center justify-between text-[8px] uppercase text-muted">
                    <span>{m.role}</span>
                    <button type="button" onClick={() => togglePin(m.id)}>
                      {pinnedIds.includes(m.id) ? "Unpin" : "Pin"}
                    </button>
                  </div>
                  <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>
                </div>
              ))}
              {!messages.length ? (
                <div className="text-[10px] text-muted">
                  Ask anything — Athena already knows this chart. Or use Quick Actions.
                </div>
              ) : null}
            </div>
            <form
              className="mt-2 flex gap-1"
              onSubmit={(e) => {
                e.preventDefault();
                if (!draft.trim() || busy) return;
                const q = draft.trim();
                setDraft("");
                void ask(q);
              }}
            >
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Ask Athena…"
                className="min-w-0 flex-1 rounded-sm border border-border bg-panel px-2 py-1 text-[11px]"
              />
              <button
                type="submit"
                disabled={busy || !draft.trim()}
                className="rounded-sm bg-primary/20 px-2 text-[10px] text-primary disabled:opacity-40"
              >
                Send
              </button>
            </form>
          </div>
        ) : null}

        {tab === "trade" ? (
          <div className="space-y-2 text-[11px]">
            <Block title="Active Plan">
              {o && o.direction !== "flat" ? (
                <div className="font-mono text-[10px]">
                  {o.direction} · {o.grade}
                  <br />
                  Entry {o.entry} SL {o.stopLoss}
                  <br />
                  TP {o.takeProfit1} / {o.takeProfit2} / {o.takeProfit3}
                  <br />
                  RR {o.riskReward} · Risk {o.riskCategory}
                  <br />
                  Exit: {o.exitAction} — {o.exitReason}
                </div>
              ) : (
                <span className="text-muted">No directional trade</span>
              )}
            </Block>
            <div className="flex flex-wrap gap-1">
              <Btn disabled={busy} onClick={() => void runQuick("review_my_trade")}>
                Review Trade
              </Btn>
              <Btn disabled={busy} onClick={() => void review()}>
                Full AI Review
              </Btn>
              <Btn disabled={busy} onClick={() => void runQuick("current_risks")}>
                Risks
              </Btn>
            </div>
            <Block title="Supporting">
              <div className="text-[10px] text-bullish">
                {(o?.supporting ?? []).join(" · ") || "—"}
              </div>
            </Block>
            <Block title="Conflicting">
              <div className="text-[10px] text-bearish">
                {(o?.opposing ?? []).join(" · ") || "—"}
              </div>
            </Block>
          </div>
        ) : null}

        {tab === "journal" ? (
          <div className="space-y-2 text-[11px]">
            <Btn disabled={busy} onClick={() => void runQuick("generate_journal")}>
              Generate Journal
            </Btn>
            <div className="whitespace-pre-wrap rounded-sm border border-border bg-panel p-2 text-[10px] text-muted">
              {journalDraft || "Journal drafts appear here after generation."}
            </div>
          </div>
        ) : null}

        {tab === "coach" ? (
          <div className="space-y-2 text-[11px]">
            <p className="text-[10px] text-muted">
              Coaching uses Decision Engine risk, RR, and opposing signals — never invents a new trade.
            </p>
            <Btn disabled={busy} onClick={() => void coach()}>
              Get Coaching
            </Btn>
            <Btn disabled={busy} onClick={() => void runQuick("detect_mistakes")}>
              Detect Mistakes
            </Btn>
            <div className="flex flex-wrap gap-1">
              {QUICK.slice(6).map((id) => (
                <Btn key={id} disabled={busy} onClick={() => void runQuick(id)}>
                  {QUICK_ACTION_LABELS[id]}
                </Btn>
              ))}
            </div>
          </div>
        ) : null}

        {tab === "history" ? (
          <div className="space-y-2 text-[11px]">
            <Block title="Pinned">
              {messages.filter((m) => m.pinned).map((m) => (
                <div key={m.id} className="mb-1 text-[10px] text-muted">
                  {m.content.slice(0, 120)}…
                </div>
              ))}
              {!messages.some((m) => m.pinned) ? (
                <span className="text-muted">No pinned messages</span>
              ) : null}
            </Block>
            <Block title="Conversations">
              {threads.slice(0, 8).map((t) => (
                <div key={t.key} className="font-mono text-[9px] text-muted">
                  {t.symbol} {t.timeframe} · {t.messages.length} msgs
                </div>
              ))}
              {!threads.length ? (
                <span className="text-muted">No saved threads yet</span>
              ) : null}
            </Block>
          </div>
        ) : null}

        {busy ? (
          <div className="mt-2 text-[10px] text-primary">Thinking…</div>
        ) : null}
        {lastError ? (
          <div className="mt-2 text-[10px] text-bearish">{lastError}</div>
        ) : null}
      </div>
    </div>
  );
}

function Block({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-sm border border-border-subtle bg-panel px-2.5 py-2">
      <div className="text-[9px] font-medium uppercase tracking-wide text-muted-foreground">
        {title}
      </div>
      <div className="mt-1">{children}</div>
    </div>
  );
}

function Btn({
  children,
  onClick,
  disabled,
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="rounded-sm border border-border px-2 py-1 text-[10px] text-muted hover:border-primary/40 hover:text-primary disabled:opacity-40"
    >
      {children}
    </button>
  );
}
