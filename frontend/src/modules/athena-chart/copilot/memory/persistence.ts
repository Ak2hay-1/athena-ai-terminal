import type { ConversationThread, CopilotMessage } from "../types";

const THREADS_KEY = "athena.chart.copilot.threads.v1";

export function conversationKey(
  symbol: string,
  timeframe: string,
  tradeId?: string | null,
): string {
  return `${symbol}:${timeframe}:${tradeId ?? "none"}`;
}

export function loadThreads(): ConversationThread[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(THREADS_KEY);
    if (raw) return JSON.parse(raw) as ConversationThread[];
  } catch {
    /* ignore */
  }
  return [];
}

export function saveThreads(threads: ConversationThread[]): void {
  try {
    localStorage.setItem(THREADS_KEY, JSON.stringify(threads.slice(-40)));
  } catch {
    /* ignore */
  }
}

export function upsertThread(
  threads: ConversationThread[],
  thread: ConversationThread,
): ConversationThread[] {
  const rest = threads.filter((t) => t.key !== thread.key);
  return [...rest, thread].sort((a, b) => b.updatedAt - a.updatedAt).slice(-40);
}

export function appendMessage(
  thread: ConversationThread,
  msg: CopilotMessage,
): ConversationThread {
  return {
    ...thread,
    messages: [...thread.messages, msg].slice(-80),
    updatedAt: Date.now(),
  };
}
