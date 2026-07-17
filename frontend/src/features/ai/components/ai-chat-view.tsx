"use client";

import { useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { MARKET_SYMBOLS, TIMEFRAMES, priceDigitsFor } from "@/constants/markets";
import { formatPercent, formatPrice } from "@/lib/utils";
import { getNewsContext } from "@/services/news";
import {
  analyzeMarket,
  getLatestRecommendation,
} from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

const suggestedPrompts = [
  "Analyze current setup",
  "Why this signal?",
  "Explain today's news risk",
  "Show risk plan",
  "Compare confidence drivers",
];

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

function buildContextReply(input: {
  prompt: string;
  symbol: string;
  timeframe: string;
  recommendation: Awaited<ReturnType<typeof getLatestRecommendation>>;
  news: Awaited<ReturnType<typeof getNewsContext>> | undefined;
  analyzeNote?: string;
}): string {
  const { prompt, symbol, timeframe, recommendation, news, analyzeNote } = input;
  const lower = prompt.toLowerCase();

  if (analyzeNote) {
    return analyzeNote;
  }

  if (!recommendation) {
    return `No live recommendation for ${symbol} ${timeframe} yet. Try “Analyze current setup” to run Athena’s pipeline.`;
  }

  const digits = priceDigitsFor(symbol, recommendation.entry);
  const plan = [
    `Signal: ${recommendation.signal} (${formatPercent(recommendation.confidence)})`,
    `Trend: ${recommendation.trend} · Risk: ${recommendation.risk}`,
    `Entry ${formatPrice(recommendation.entry, digits)} · SL ${formatPrice(recommendation.stopLoss, digits)} · TP ${formatPrice(recommendation.takeProfit, digits)}`,
    `RR ${recommendation.riskReward.toFixed(2)}x`,
  ].join("\n");

  if (lower.includes("why") || lower.includes("signal") || lower.includes("reason")) {
    const reasons =
      recommendation.reasons.length > 0
        ? recommendation.reasons.map((r) => `• ${r}`).join("\n")
        : "• Confluence and structure currently favor this bias.";
    return `${plan}\n\nDrivers:\n${reasons}`;
  }

  if (lower.includes("news") || lower.includes("risk window") || lower.includes("calendar")) {
    const headlines =
      news?.headlines?.length
        ? news.headlines.slice(0, 4).map((h) => `• ${h}`).join("\n")
        : "• No headline context loaded.";
    return [
      `News sentiment for ${symbol}: ${news?.sentiment ?? "NEUTRAL"} (score ${news?.score ?? 0}).`,
      news?.highImpactUpcoming
        ? "High-impact event window is approaching — size down or wait."
        : "No immediate high-impact block flagged.",
      "",
      "Headlines:",
      headlines,
    ].join("\n");
  }

  if (lower.includes("risk") || lower.includes("plan") || lower.includes("sl") || lower.includes("tp")) {
    return `${plan}\n\nUse the stop as hard invalidation. Athena evaluates — you decide size and timing.`;
  }

  return `${plan}\n\nAsk about reasons, news risk, or run a fresh analysis.`;
}

export function AiChatView() {
  const user = useAuthStore((s) => s.user);
  const symbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Athena AI is connected to live recommendations and news context. Ask about setups, risk, or run an analysis.",
    },
  ]);

  const recommendationQuery = useQuery({
    queryKey: ["recommendation", "latest", symbol, timeframe],
    queryFn: () => getLatestRecommendation(symbol, timeframe),
    enabled: Boolean(user),
    refetchInterval: 60_000,
  });

  const newsQuery = useQuery({
    queryKey: ["news", "context", symbol],
    queryFn: () => getNewsContext(symbol),
    enabled: Boolean(user),
    refetchInterval: 30_000,
  });

  const analyzeMutation = useMutation({
    mutationFn: () => analyzeMarket(symbol, timeframe),
  });

  const contextBadge = useMemo(() => {
    const rec = recommendationQuery.data;
    if (!rec) return "Awaiting signal";
    return `${rec.signal} · ${formatPercent(rec.confidence)}`;
  }, [recommendationQuery.data]);

  async function respond(prompt: string) {
    const trimmed = prompt.trim();
    if (!trimmed) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: trimmed,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    let analyzeNote: string | undefined;
    const wantsAnalyze =
      /analyze|run analysis|current setup|fresh/i.test(trimmed);

    if (wantsAnalyze) {
      try {
        const result = await analyzeMutation.mutateAsync();
        if (result.recommendation) {
          await recommendationQuery.refetch();
          const digits = priceDigitsFor(symbol, result.recommendation.entry);
          analyzeNote = [
            result.message ?? "Analysis complete.",
            `Signal ${result.recommendation.signal} at ${formatPercent(result.recommendation.confidence)}.`,
            `Entry ${formatPrice(result.recommendation.entry, digits)} · SL ${formatPrice(result.recommendation.stopLoss, digits)} · TP ${formatPrice(result.recommendation.takeProfit, digits)}.`,
          ].join(" ");
        } else {
          analyzeNote = result.message ?? "Analysis finished without a new recommendation.";
        }
      } catch (error) {
        analyzeNote =
          error instanceof Error ? error.message : "Analysis failed. Try again.";
      }
    }

    const reply = buildContextReply({
      prompt: trimmed,
      symbol,
      timeframe,
      recommendation: recommendationQuery.data ?? null,
      news: newsQuery.data,
      analyzeNote,
    });

    setMessages((prev) => [
      ...prev,
      {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: reply,
      },
    ]);
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void respond(input);
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-[1100px] flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Athena AI
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Market assistant</h1>
          <p className="mt-1 text-sm text-muted">
            Live context for {symbol} {timeframe} · news-aware replies
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="ai">{contextBadge}</Badge>
          <Badge tone={newsQuery.data?.highImpactUpcoming ? "warning" : "neutral"}>
            News {newsQuery.data?.sentiment ?? "—"}
          </Badge>
          <select
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
            className="h-9 rounded-sm border border-border bg-panel px-3 font-mono text-sm outline-none focus:border-primary/50"
          >
            {MARKET_SYMBOLS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select
            value={timeframe}
            onChange={(event) => setTimeframe(event.target.value)}
            className="h-9 rounded-sm border border-border bg-panel px-3 font-mono text-sm outline-none focus:border-primary/50"
          >
            {TIMEFRAMES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </div>

      <Card className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <CardContent className="flex min-h-0 flex-1 flex-col gap-4 p-4">
          <div className="flex flex-wrap gap-1.5">
            {suggestedPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => void respond(prompt)}
                className="rounded-sm border border-border bg-background/40 px-2.5 py-1 text-[11px] text-muted transition-colors hover:border-ai/30 hover:text-foreground"
              >
                {prompt}
              </button>
            ))}
          </div>

          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
            {messages.map((message) => (
              <div
                key={message.id}
                className={
                  message.role === "user"
                    ? "ml-auto max-w-[85%] rounded-sm border border-primary/25 bg-primary/10 px-3 py-2 text-sm whitespace-pre-wrap"
                    : "mr-auto max-w-[90%] rounded-sm border border-ai/20 bg-ai/5 px-3 py-2 text-sm whitespace-pre-wrap text-zinc-200"
                }
              >
                {message.role === "assistant" ? (
                  <span className="mb-1 flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-ai">
                    <Sparkles className="h-3 w-3" /> Athena
                  </span>
                ) : null}
                {message.content}
              </div>
            ))}
          </div>

          <form onSubmit={onSubmit} className="flex gap-2 border-t border-border pt-3">
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={`Ask about ${symbol}…`}
              className="h-10 flex-1 rounded-sm border border-border bg-background/40 px-3 text-sm outline-none placeholder:text-muted-foreground focus:border-ai/40"
            />
            <Button variant="ai" type="submit" disabled={analyzeMutation.isPending}>
              {analyzeMutation.isPending ? "Working…" : "Send"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
