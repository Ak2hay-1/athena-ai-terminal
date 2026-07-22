"use client";

import { useMemo, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { getSuggestedPrompts } from "@/lib/ai-prompts";
import { chatWithAthena } from "@/services/ai";
import { getLatestRecommendation } from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";
import { useUiStore } from "@/store/ui-store";

export function AiAssistantPanel() {
  const router = useRouter();
  const rightPanel = useUiStore((s) => s.rightPanel);
  const user = useAuthStore((s) => s.user);
  const symbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const [input, setInput] = useState("");
  const [reply, setReply] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recommendationQuery = useQuery({
    queryKey: ["recommendation", "latest", symbol],
    queryFn: () => getLatestRecommendation(symbol),
    enabled: Boolean(user) && rightPanel === "assistant",
    staleTime: 30_000,
  });

  const suggestedPrompts = useMemo(
    () =>
      getSuggestedPrompts(symbol, timeframe, recommendationQuery.data?.signal),
    [recommendationQuery.data?.signal, symbol, timeframe],
  );

  if (rightPanel !== "assistant") return null;

  async function ask(prompt: string) {
    const trimmed = prompt.trim();
    if (!trimmed || pending) return;

    setPending(true);
    setError(null);
    setInput("");

    try {
      const result = await chatWithAthena({
        messages: [{ role: "user", content: trimmed }],
        symbol,
        timeframe,
      });
      setReply(result.reply);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed.");
    } finally {
      setPending(false);
    }
  }

  function goToChat(prompt?: string) {
    const q = prompt?.trim();
    if (q) {
      router.push(`/ai?q=${encodeURIComponent(q)}`);
      return;
    }
    router.push("/ai");
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void ask(input);
  }

  return (
    <aside className="hidden h-[calc(100dvh-3.5rem)] w-[300px] shrink-0 flex-col border-l border-border bg-sidebar xl:flex">
      <div className="flex h-12 shrink-0 items-center gap-2 border-b border-border px-3">
        <span className="flex h-7 w-7 items-center justify-center rounded-sm bg-ai/15">
          <Sparkles className="h-3.5 w-3.5 text-ai" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">AI Assistant</p>
          <p className="truncate text-[11px] text-muted">
            {symbol} · {timeframe}
          </p>
        </div>
        <button
          type="button"
          onClick={() => goToChat()}
          className="text-[11px] text-primary hover:underline"
        >
          Full chat
        </button>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-3">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="rounded-sm border border-ai/20 bg-ai/5 p-3 text-sm leading-relaxed text-zinc-300"
        >
          {reply ??
            `Context loaded for ${symbol}. Ask about this pair setup, risk, or news window.`}
        </motion.div>

        {error ? (
          <p className="text-xs text-bearish">{error}</p>
        ) : null}
        {pending ? (
          <p className="text-xs text-muted-foreground">Athena is thinking…</p>
        ) : null}

        <div>
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Suggested for {symbol}
          </p>
          <div className="flex flex-col gap-1.5">
            {suggestedPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                disabled={pending}
                onClick={() => void ask(prompt)}
                className="rounded-sm border border-border bg-panel px-3 py-2 text-left text-xs text-muted transition-colors hover:border-ai/30 hover:bg-ai/5 hover:text-foreground disabled:opacity-50"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>

      <form
        onSubmit={onSubmit}
        className="shrink-0 border-t border-border p-3"
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={`Ask about ${symbol}…`}
            disabled={pending}
            className="h-9 flex-1 rounded-sm border border-border bg-panel px-3 text-sm outline-none placeholder:text-muted-foreground focus:border-ai/40 focus:ring-2 focus:ring-ai/15 disabled:opacity-50"
          />
          <Button variant="ai" size="sm" type="submit" disabled={pending || !input.trim()}>
            Send
          </Button>
        </div>
      </form>
    </aside>
  );
}
