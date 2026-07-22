"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { MARKET_SYMBOLS, TIMEFRAMES, priceDigitsFor } from "@/constants/markets";
import {
  AiChat,
  type AiChatBubble,
} from "@/features/ai/components/ai-chat";
import { MarketSummary } from "@/features/ai/components/market-summary";
import { getSuggestedPrompts } from "@/lib/ai-prompts";
import { formatPercent, formatPrice } from "@/lib/utils";
import { chatWithAthena } from "@/services/ai";
import { getNewsContext } from "@/services/news";
import {
  analyzeMarket,
  getLatestRecommendation,
} from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

export function AiChatView() {
  const user = useAuthStore((s) => s.user);
  const symbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);
  const searchParams = useSearchParams();
  const bootstrappedQ = useRef(false);
  const [messages, setMessages] = useState<AiChatBubble[]>([
    {
      id: "welcome",
      role: "assistant",
      content: `Athena AI is loaded for ${symbol} ${timeframe}. Ask about setups, risk, or run an analysis.`,
    },
  ]);

  const recommendationQuery = useQuery({
    queryKey: ["recommendation", "latest", symbol],
    queryFn: () => getLatestRecommendation(symbol),
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

  const suggestedPrompts = useMemo(
    () =>
      getSuggestedPrompts(symbol, timeframe, recommendationQuery.data?.signal),
    [recommendationQuery.data?.signal, symbol, timeframe],
  );

  const contextBadge = useMemo(() => {
    const rec = recommendationQuery.data;
    if (!rec) return "Awaiting signal";
    return `${rec.signal} · ${formatPercent(rec.confidence)}`;
  }, [recommendationQuery.data]);

  useEffect(() => {
    const q = searchParams.get("q")?.trim();
    if (!q || bootstrappedQ.current) return;
    bootstrappedQ.current = true;

    const userMsg: AiChatBubble = {
      id: `u-q-${Date.now()}`,
      role: "user",
      content: q,
    };
    setMessages((prev) => [...prev, userMsg]);

    void (async () => {
      try {
        const result = await chatWithAthena({
          messages: [{ role: "user", content: q }],
          symbol,
          timeframe,
        });
        setMessages((prev) => [
          ...prev,
          {
            id: `a-q-${Date.now()}`,
            role: "assistant",
            content: result.reply,
          },
        ]);
      } catch (error) {
        setMessages((prev) => [
          ...prev,
          {
            id: `a-q-err-${Date.now()}`,
            role: "assistant",
            content:
              error instanceof Error
                ? error.message
                : "Chat request failed.",
          },
        ]);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setMessages((prev) => {
      if (prev.length !== 1 || prev[0]?.id !== "welcome") return prev;
      return [
        {
          id: "welcome",
          role: "assistant",
          content: `Athena AI is loaded for ${symbol} ${timeframe}. Ask about setups, risk, or run an analysis.`,
        },
      ];
    });
  }, [symbol, timeframe]);

  return (
    <div className="mx-auto flex h-[min(720px,calc(100dvh-7.5rem))] max-w-[960px] flex-col gap-3">
      <div className="flex shrink-0 flex-wrap items-end justify-between gap-3 border-b border-border pb-3">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Athena AI
          </p>
          <h1 className="mt-1 text-xl font-semibold tracking-tight">
            Market assistant
          </h1>
          <p className="mt-0.5 text-xs text-muted">
            Local LLM explains frozen Athena decisions · {symbol} {timeframe}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="ai">{contextBadge}</Badge>
          <Badge
            tone={newsQuery.data?.highImpactUpcoming ? "warning" : "neutral"}
          >
            News {newsQuery.data?.sentiment ?? "—"}
          </Badge>
          <select
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
            className="h-8 rounded-sm border border-border bg-panel px-2.5 font-mono text-xs outline-none focus:border-primary/50"
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
            className="h-8 rounded-sm border border-border bg-panel px-2.5 font-mono text-xs outline-none focus:border-primary/50"
          >
            {TIMEFRAMES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </div>

      <MarketSummary symbol={symbol} timeframe={timeframe} compact />

      <Card className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <CardContent className="flex min-h-0 flex-1 flex-col p-3">
          <AiChat
            symbol={symbol}
            timeframe={timeframe}
            messages={messages}
            onMessagesChange={setMessages}
            suggestedPrompts={suggestedPrompts}
            preferStream
            onBeforeSend={async (trimmed) => {
              const wantsAnalyze =
                /analyze|run analysis|current setup|fresh/i.test(trimmed);
              if (!wantsAnalyze) return;
              try {
                const result = await analyzeMutation.mutateAsync();
                if (result.recommendation) {
                  await recommendationQuery.refetch();
                  const digits = priceDigitsFor(
                    symbol,
                    result.recommendation.entry,
                  );
                  const analyzeNote = [
                    result.message ?? "Analysis complete.",
                    `Signal ${result.recommendation.signal} at ${formatPercent(result.recommendation.confidence)}.`,
                    `Entry ${formatPrice(result.recommendation.entry, digits)} · SL ${formatPrice(result.recommendation.stopLoss, digits)} · TP ${formatPrice(result.recommendation.takeProfit, digits)}.`,
                  ].join(" ");
                  setMessages((prev) => [
                    ...prev,
                    {
                      id: `a-analyze-${Date.now()}`,
                      role: "assistant",
                      content: analyzeNote,
                    },
                  ]);
                }
              } catch (error) {
                setMessages((prev) => [
                  ...prev,
                  {
                    id: `a-analyze-err-${Date.now()}`,
                    role: "assistant",
                    content:
                      error instanceof Error
                        ? error.message
                        : "Analysis failed. Try again.",
                  },
                ]);
              }
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
