"use client";

import { useState, type FormEvent, type ReactNode } from "react";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AiMarkdown } from "@/features/ai/components/ai-markdown";
import { useAiStream } from "@/hooks/use-ai-stream";
import { chatWithAthena, type AiChatMessage } from "@/services/ai";

export type AiChatBubble = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type Props = {
  symbol?: string;
  timeframe?: string;
  messages: AiChatBubble[];
  onMessagesChange: (messages: AiChatBubble[]) => void;
  suggestedPrompts?: string[];
  header?: ReactNode;
  preferStream?: boolean;
  onBeforeSend?: (prompt: string) => Promise<void> | void;
  className?: string;
};

export function AiChat({
  symbol,
  timeframe,
  messages,
  onMessagesChange,
  suggestedPrompts = [],
  header,
  preferStream = true,
  onBeforeSend,
  className,
}: Props) {
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const { connected, streaming, sendChat } = useAiStream(preferStream);

  async function respond(prompt: string) {
    const trimmed = prompt.trim();
    if (!trimmed || pending || streaming) return;

    const userMsg: AiChatBubble = {
      id: `u-${Date.now()}`,
      role: "user",
      content: trimmed,
    };
    const nextMessages = [...messages, userMsg];
    onMessagesChange(nextMessages);
    setInput("");
    setPending(true);

    try {
      await onBeforeSend?.(trimmed);

      const history: AiChatMessage[] = nextMessages
        .filter((m) => m.id !== "welcome")
        .map((m) => ({ role: m.role, content: m.content }))
        .slice(-20);

      const assistantId = `a-${Date.now()}`;

      if (preferStream && connected) {
        onMessagesChange([
          ...nextMessages,
          { id: assistantId, role: "assistant", content: "" },
        ]);

        await new Promise<void>((resolve) => {
          const requestId = sendChat(
            { messages: history, symbol, timeframe },
            {
              onChunk: (_delta, full) => {
                onMessagesChange([
                  ...nextMessages,
                  { id: assistantId, role: "assistant", content: full },
                ]);
              },
              onDone: (full) => {
                onMessagesChange([
                  ...nextMessages,
                  {
                    id: assistantId,
                    role: "assistant",
                    content: full || "No reply from Athena.",
                  },
                ]);
                resolve();
              },
              onError: (message) => {
                onMessagesChange([
                  ...nextMessages,
                  { id: assistantId, role: "assistant", content: message },
                ]);
                resolve();
              },
            },
          );
          if (!requestId) {
            void chatWithAthena({ messages: history, symbol, timeframe }).then(
              (result) => {
                onMessagesChange([
                  ...nextMessages,
                  {
                    id: assistantId,
                    role: "assistant",
                    content: result.reply,
                  },
                ]);
                resolve();
              },
            );
          }
        });
      } else {
        const result = await chatWithAthena({
          messages: history,
          symbol,
          timeframe,
        });
        onMessagesChange([
          ...nextMessages,
          {
            id: assistantId,
            role: "assistant",
            content: result.reply,
          },
        ]);
      }
    } catch (error) {
      onMessagesChange([
        ...nextMessages,
        {
          id: `a-err-${Date.now()}`,
          role: "assistant",
          content:
            error instanceof Error
              ? error.message
              : "Chat request failed. Check AI provider configuration.",
        },
      ]);
    } finally {
      setPending(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void respond(input);
  }

  const busy = pending || streaming;

  return (
    <div className={className ?? "flex min-h-0 flex-1 flex-col gap-3"}>
      {header}

      {suggestedPrompts.length > 0 ? (
        <div className="flex shrink-0 flex-wrap gap-1.5">
          {suggestedPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              disabled={busy}
              onClick={() => void respond(prompt)}
              className="rounded-sm border border-border bg-background/40 px-2.5 py-1 text-[11px] text-muted transition-colors hover:border-ai/30 hover:text-foreground disabled:opacity-50"
            >
              {prompt}
            </button>
          ))}
        </div>
      ) : null}

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
        {messages.map((message) => (
          <div
            key={message.id}
            className={
              message.role === "user"
                ? "ml-auto max-w-[85%] rounded-sm border border-primary/25 bg-primary/10 px-3 py-2 text-sm whitespace-pre-wrap"
                : "mr-auto max-w-[90%] rounded-sm border border-ai/20 bg-ai/5 px-3 py-2"
            }
          >
            {message.role === "assistant" ? (
              <span className="mb-1 flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-ai">
                <Sparkles className="h-3 w-3" /> Athena
              </span>
            ) : null}
            {message.role === "assistant" ? (
              <AiMarkdown content={message.content || (busy ? "…" : "")} />
            ) : (
              message.content
            )}
          </div>
        ))}
        {busy ? (
          <p className="text-xs text-muted-foreground">
            Athena is {streaming ? "streaming" : "thinking"}…
            {preferStream ? (
              <span className="ml-2 text-muted">
                WS {connected ? "connected" : "offline · HTTP fallback"}
              </span>
            ) : null}
          </p>
        ) : null}
      </div>

      <form
        onSubmit={onSubmit}
        className="flex shrink-0 gap-2 border-t border-border pt-3"
      >
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={symbol ? `Ask about ${symbol}…` : "Ask Athena…"}
          disabled={busy}
          className="h-10 flex-1 rounded-sm border border-border bg-background/40 px-3 text-sm outline-none placeholder:text-muted-foreground focus:border-ai/40 disabled:opacity-50"
        />
        <Button variant="ai" type="submit" disabled={busy || !input.trim()}>
          Send
        </Button>
      </form>
    </div>
  );
}
