import { create } from "zustand";
import type {
  AnalysisSnapshot,
  IntelligenceEvent,
  IntelligenceSettings,
  OverlayVisibility,
} from "../types";
import { DEFAULT_INTEL_SETTINGS } from "../types";

interface IntelligenceState {
  snapshot: AnalysisSnapshot | null;
  settings: IntelligenceSettings;
  events: IntelligenceEvent[];
  analyzing: boolean;
  lastError: string | null;
  setSnapshot: (snap: AnalysisSnapshot | null) => void;
  appendEvents: (events: IntelligenceEvent[]) => void;
  setSettings: (partial: Partial<IntelligenceSettings>) => void;
  setOverlay: (key: keyof OverlayVisibility, value: boolean) => void;
  setAnalyzing: (v: boolean) => void;
  setError: (e: string | null) => void;
}

const SETTINGS_KEY = "athena.chart.intel.settings.v1";

function loadSettings(): IntelligenceSettings {
  if (typeof window === "undefined") return { ...DEFAULT_INTEL_SETTINGS, overlays: { ...DEFAULT_INTEL_SETTINGS.overlays } };
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as IntelligenceSettings;
      return {
        ...DEFAULT_INTEL_SETTINGS,
        ...parsed,
        overlays: { ...DEFAULT_INTEL_SETTINGS.overlays, ...parsed.overlays },
      };
    }
  } catch {
    /* ignore */
  }
  return { ...DEFAULT_INTEL_SETTINGS, overlays: { ...DEFAULT_INTEL_SETTINGS.overlays } };
}

export const useIntelligenceStore = create<IntelligenceState>((set, get) => ({
  snapshot: null,
  settings: loadSettings(),
  events: [],
  analyzing: false,
  lastError: null,
  setSnapshot: (snapshot) => {
    set({ snapshot });
    if (snapshot?.events?.length) {
      get().appendEvents(snapshot.events);
    }
  },
  appendEvents: (events) =>
    set((s) => {
      const map = new Map<string, IntelligenceEvent>();
      for (const e of [...s.events, ...events]) {
        map.set(`${e.kind}:${e.time}:${e.label}`, e);
      }
      return { events: [...map.values()].sort((a, b) => a.timeSec - b.timeSec).slice(-80) };
    }),
  setSettings: (partial) => {
    const settings = {
      ...get().settings,
      ...partial,
      overlays: { ...get().settings.overlays, ...(partial.overlays ?? {}) },
    };
    set({ settings });
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    } catch {
      /* ignore */
    }
  },
  setOverlay: (key, value) => {
    get().setSettings({ overlays: { ...get().settings.overlays, [key]: value } });
  },
  setAnalyzing: (analyzing) => set({ analyzing }),
  setError: (lastError) => set({ lastError }),
}));
