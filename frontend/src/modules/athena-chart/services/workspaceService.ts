import type { DrawingObject } from "../types";
import type { IndicatorInstance } from "../engine/indicators/types";
import type { WatchlistItem } from "../store/watchlist-store";
import type { ViewportState } from "../types";

const KEY = "athena.chart.workspace.v1";

export interface ChartWorkspace {
  version: 1;
  symbol: string;
  timeframe: string;
  theme: "dark" | "light";
  viewport: ViewportState;
  drawings: DrawingObject[];
  indicators: IndicatorInstance[];
  watchlist: WatchlistItem[];
  sessionsEnabled: boolean;
  sessionFlags: Record<string, boolean>;
  liveMode?: boolean;
  savedAt: number;
}

export function saveWorkspace(ws: ChartWorkspace): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(ws));
  } catch {
    /* quota */
  }
}

export function loadWorkspace(): ChartWorkspace | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ChartWorkspace;
  } catch {
    return null;
  }
}

export function clearWorkspace(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}

export const workspaceService = {
  save: saveWorkspace,
  load: loadWorkspace,
  clear: clearWorkspace,
  key: KEY,
};
