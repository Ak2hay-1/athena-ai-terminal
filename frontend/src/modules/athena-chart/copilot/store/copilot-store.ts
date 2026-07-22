import { create } from "zustand";
import type {
  CopilotMessage,
  CopilotSettings,
  CopilotTab,
  ExplainTarget,
  ConversationThread,
} from "../types";
import { DEFAULT_COPILOT_SETTINGS } from "../types";
import {
  appendMessage,
  conversationKey,
  loadThreads,
  saveThreads,
  upsertThread,
} from "../memory/persistence";

interface CopilotState {
  tab: CopilotTab;
  settings: CopilotSettings;
  messages: CopilotMessage[];
  pinnedIds: string[];
  selectedObject: ExplainTarget | null;
  busy: boolean;
  lastError: string | null;
  journalDraft: string | null;
  lastInsights: string | null;
  threads: ConversationThread[];
  activeKey: string | null;
  setTab: (tab: CopilotTab) => void;
  setSettings: (partial: Partial<CopilotSettings>) => void;
  setSelectedObject: (obj: ExplainTarget | null) => void;
  setBusy: (v: boolean) => void;
  setError: (e: string | null) => void;
  loadConversation: (symbol: string, timeframe: string, tradeId?: string | null) => void;
  pushMessage: (msg: CopilotMessage) => void;
  togglePin: (id: string) => void;
  setJournalDraft: (text: string | null) => void;
  setLastInsights: (text: string | null) => void;
  clearChat: () => void;
}

const SETTINGS_KEY = "athena.chart.copilot.settings.v1";

function loadSettings(): CopilotSettings {
  if (typeof window === "undefined") return { ...DEFAULT_COPILOT_SETTINGS };
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) return { ...DEFAULT_COPILOT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return { ...DEFAULT_COPILOT_SETTINGS };
}

export const useCopilotStore = create<CopilotState>((set, get) => ({
  tab: "overview",
  settings: loadSettings(),
  messages: [],
  pinnedIds: [],
  selectedObject: null,
  busy: false,
  lastError: null,
  journalDraft: null,
  lastInsights: null,
  threads: typeof window !== "undefined" ? loadThreads() : [],
  activeKey: null,

  setTab: (tab) => set({ tab }),
  setSettings: (partial) => {
    const settings = { ...get().settings, ...partial };
    set({ settings });
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    } catch {
      /* ignore */
    }
  },
  setSelectedObject: (selectedObject) => set({ selectedObject }),
  setBusy: (busy) => set({ busy }),
  setError: (lastError) => set({ lastError }),

  loadConversation: (symbol, timeframe, tradeId) => {
    const key = conversationKey(symbol, timeframe, tradeId);
    const threads = get().threads.length ? get().threads : loadThreads();
    const existing = threads.find((t) => t.key === key);
    set({
      threads,
      activeKey: key,
      messages: existing?.messages ?? [],
      pinnedIds: (existing?.messages ?? []).filter((m) => m.pinned).map((m) => m.id),
    });
  },

  pushMessage: (msg) => {
    const { activeKey, messages, threads } = get();
    const nextMessages = [...messages, msg].slice(-80);
    set({ messages: nextMessages });
    if (!activeKey) return;
    const [symbol, timeframe, tradePart] = activeKey.split(":");
    const base =
      threads.find((t) => t.key === activeKey) ??
      ({
        key: activeKey,
        symbol,
        timeframe,
        tradeId: tradePart === "none" ? null : tradePart,
        messages: [],
        updatedAt: Date.now(),
      } satisfies ConversationThread);
    const updated = appendMessage({ ...base, messages: nextMessages.slice(0, -1) }, msg);
    const nextThreads = upsertThread(threads, updated);
    set({ threads: nextThreads });
    saveThreads(nextThreads);
  },

  togglePin: (id) => {
    const messages = get().messages.map((m) =>
      m.id === id ? { ...m, pinned: !m.pinned } : m,
    );
    set({
      messages,
      pinnedIds: messages.filter((m) => m.pinned).map((m) => m.id),
    });
  },

  setJournalDraft: (journalDraft) => set({ journalDraft }),
  setLastInsights: (lastInsights) => set({ lastInsights }),
  clearChat: () => set({ messages: [], pinnedIds: [] }),
}));
