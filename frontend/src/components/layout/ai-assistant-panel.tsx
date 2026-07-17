"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUiStore } from "@/store/ui-store";

const suggestedPrompts = [
  "Analyze Gold",
  "Why BUY?",
  "Explain today's setup",
  "Show H4 Trend",
  "Compare Gold vs BTC",
];

export function AiAssistantPanel() {
  const rightPanel = useUiStore((s) => s.rightPanel);

  if (rightPanel !== "assistant") return null;

  return (
    <aside className="hidden w-[320px] shrink-0 border-l border-border bg-sidebar xl:flex xl:flex-col">
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-ai/15">
          <Sparkles className="h-3.5 w-3.5 text-ai" />
        </span>
        <div>
          <p className="text-sm font-medium">AI Assistant</p>
          <p className="text-[11px] text-muted">Market context loaded</p>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="rounded-xl border border-ai/20 bg-ai/5 p-3 text-sm leading-relaxed text-zinc-300"
        >
          I already have today&apos;s structure, liquidity, and confluence for your
          watchlist. Ask about a setup, risk, or comparison.
        </motion.div>

        <div>
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Suggested
          </p>
          <div className="flex flex-col gap-1.5">
            {suggestedPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="rounded-lg border border-border bg-panel px-3 py-2 text-left text-xs text-muted transition-colors hover:border-ai/30 hover:bg-ai/5 hover:text-foreground"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="border-t border-border p-3">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Ask Athena…"
            className="h-9 flex-1 rounded-lg border border-border bg-panel px-3 text-sm outline-none placeholder:text-muted-foreground focus:border-ai/40 focus:ring-2 focus:ring-ai/15"
          />
          <Button variant="ai" size="sm">
            Send
          </Button>
        </div>
      </div>
    </aside>
  );
}
