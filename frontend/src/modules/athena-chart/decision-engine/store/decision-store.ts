import { create } from "zustand";
import type {
  DecisionEvent,
  DecisionMemoryRecord,
  DecisionSettings,
  DecisionSnapshot,
  DecisionOverlayVisibility,
  SignalWeights,
  TradeOpportunity,
} from "../types";
import { DEFAULT_DECISION_SETTINGS } from "../types";

interface DecisionState {
  snapshot: DecisionSnapshot | null;
  opportunity: TradeOpportunity | null;
  settings: DecisionSettings;
  events: DecisionEvent[];
  memory: DecisionMemoryRecord[];
  deciding: boolean;
  lastError: string | null;
  setSnapshot: (snap: DecisionSnapshot | null) => void;
  appendEvents: (events: DecisionEvent[]) => void;
  appendMemory: (records: DecisionMemoryRecord[]) => void;
  setSettings: (partial: Partial<DecisionSettings>) => void;
  setOverlay: (key: keyof DecisionOverlayVisibility, value: boolean) => void;
  setWeight: (key: keyof SignalWeights, value: number) => void;
  setDeciding: (v: boolean) => void;
  setError: (e: string | null) => void;
}

const SETTINGS_KEY = "athena.chart.decision.settings.v1";
const MEMORY_KEY = "athena.chart.decision.memory.v1";

function loadSettings(): DecisionSettings {
  if (typeof window === "undefined") {
    return {
      ...DEFAULT_DECISION_SETTINGS,
      signalWeights: { ...DEFAULT_DECISION_SETTINGS.signalWeights },
      overlays: { ...DEFAULT_DECISION_SETTINGS.overlays },
    };
  }
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as DecisionSettings;
      return {
        ...DEFAULT_DECISION_SETTINGS,
        ...parsed,
        signalWeights: {
          ...DEFAULT_DECISION_SETTINGS.signalWeights,
          ...parsed.signalWeights,
        },
        overlays: {
          ...DEFAULT_DECISION_SETTINGS.overlays,
          ...parsed.overlays,
        },
      };
    }
  } catch {
    /* ignore */
  }
  return {
    ...DEFAULT_DECISION_SETTINGS,
    signalWeights: { ...DEFAULT_DECISION_SETTINGS.signalWeights },
    overlays: { ...DEFAULT_DECISION_SETTINGS.overlays },
  };
}

function loadMemory(): DecisionMemoryRecord[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(MEMORY_KEY);
    if (raw) return JSON.parse(raw) as DecisionMemoryRecord[];
  } catch {
    /* ignore */
  }
  return [];
}

function persistMemory(memory: DecisionMemoryRecord[]): void {
  try {
    localStorage.setItem(MEMORY_KEY, JSON.stringify(memory.slice(-200)));
  } catch {
    /* ignore */
  }
}

export const useDecisionStore = create<DecisionState>((set, get) => ({
  snapshot: null,
  opportunity: null,
  settings: loadSettings(),
  events: [],
  memory: loadMemory(),
  deciding: false,
  lastError: null,
  setSnapshot: (snapshot) => {
    set({ snapshot, opportunity: snapshot?.opportunity ?? null });
    if (snapshot?.events?.length) get().appendEvents(snapshot.events);
  },
  appendEvents: (events) =>
    set((s) => {
      const map = new Map<string, DecisionEvent>();
      for (const e of [...s.events, ...events]) {
        map.set(`${e.kind}:${e.time}:${e.label}`, e);
      }
      return {
        events: [...map.values()].sort((a, b) => a.timeSec - b.timeSec).slice(-100),
      };
    }),
  appendMemory: (records) => {
    const memory = [...get().memory, ...records].slice(-200);
    set({ memory });
    persistMemory(memory);
  },
  setSettings: (partial) => {
    const settings = {
      ...get().settings,
      ...partial,
      signalWeights: {
        ...get().settings.signalWeights,
        ...(partial.signalWeights ?? {}),
      },
      overlays: {
        ...get().settings.overlays,
        ...(partial.overlays ?? {}),
      },
    };
    set({ settings });
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    } catch {
      /* ignore */
    }
  },
  setOverlay: (key, value) => {
    get().setSettings({
      overlays: { ...get().settings.overlays, [key]: value },
    });
  },
  setWeight: (key, value) => {
    get().setSettings({
      signalWeights: { ...get().settings.signalWeights, [key]: value },
    });
  },
  setDeciding: (deciding) => set({ deciding }),
  setError: (lastError) => set({ lastError }),
}));
