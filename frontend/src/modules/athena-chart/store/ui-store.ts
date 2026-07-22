import { create } from "zustand";
import type { SmartCursorInfo } from "../types";

interface ChartUiState {
  aiPanelOpen: boolean;
  rightTab: "ai" | "watchlist";
  timelineVisible: boolean;
  timelineHeight: number;
  theme: "dark" | "light";
  fullscreen: boolean;
  searchOpen: boolean;
  settingsOpen: boolean;
  layoutMode: "single" | "split";
  hoverPrice: number | null;
  smartCursor: SmartCursorInfo | null;
  fps: number;
  setAiPanelOpen: (open: boolean) => void;
  toggleAiPanel: () => void;
  setRightTab: (tab: "ai" | "watchlist") => void;
  setTimelineVisible: (v: boolean) => void;
  setTheme: (theme: "dark" | "light") => void;
  toggleTheme: () => void;
  setFullscreen: (v: boolean) => void;
  setSearchOpen: (v: boolean) => void;
  setSettingsOpen: (v: boolean) => void;
  setLayoutMode: (mode: "single" | "split") => void;
  setHoverPrice: (price: number | null) => void;
  setSmartCursor: (info: SmartCursorInfo | null) => void;
  setFps: (fps: number) => void;
}

export const useChartUiStore = create<ChartUiState>((set) => ({
  aiPanelOpen: true,
  rightTab: "ai",
  timelineVisible: true,
  timelineHeight: 56,
  theme: "dark",
  fullscreen: false,
  searchOpen: false,
  settingsOpen: false,
  layoutMode: "single",
  hoverPrice: null,
  smartCursor: null,
  fps: 0,
  setAiPanelOpen: (aiPanelOpen) => set({ aiPanelOpen }),
  toggleAiPanel: () => set((s) => ({ aiPanelOpen: !s.aiPanelOpen })),
  setRightTab: (rightTab) => set({ rightTab, aiPanelOpen: true }),
  setTimelineVisible: (timelineVisible) => set({ timelineVisible }),
  setTheme: (theme) => set({ theme }),
  toggleTheme: () =>
    set((s) => ({ theme: s.theme === "dark" ? "light" : "dark" })),
  setFullscreen: (fullscreen) => set({ fullscreen }),
  setSearchOpen: (searchOpen) => set({ searchOpen }),
  setSettingsOpen: (settingsOpen) => set({ settingsOpen }),
  setLayoutMode: (layoutMode) => set({ layoutMode }),
  setHoverPrice: (hoverPrice) => set({ hoverPrice }),
  setSmartCursor: (smartCursor) => set({ smartCursor }),
  setFps: (fps) => set({ fps }),
}));
