import { create } from "zustand";
import type { IndicatorInstance, IndicatorSettings } from "../engine/indicators/types";
import { getIndicatorPlugin, listIndicatorPlugins } from "../engine/indicators/registry";
import { uid } from "../utils/uid";
import { DEFAULT_INDICATORS, type IndicatorFlags } from "../types";

interface IndicatorState {
  /** Legacy boolean flags — kept for Markets / ChartController pane layout */
  flags: IndicatorFlags;
  instances: IndicatorInstance[];
  favorites: string[];
  search: string;
  panelOpen: boolean;
  menuOpen: boolean;
  toggleFlag: (key: keyof IndicatorFlags) => void;
  setFlags: (flags: IndicatorFlags) => void;
  setMenuOpen: (open: boolean) => void;
  setPanelOpen: (open: boolean) => void;
  setSearch: (q: string) => void;
  addInstance: (pluginId: string) => void;
  removeInstance: (instanceId: string) => void;
  duplicateInstance: (instanceId: string) => void;
  updateInstance: (instanceId: string, settings: Partial<IndicatorSettings>) => void;
  toggleFavorite: (pluginId: string) => void;
  setInstances: (instances: IndicatorInstance[]) => void;
}

export const useIndicatorStore = create<IndicatorState>((set, get) => ({
  flags: { ...DEFAULT_INDICATORS },
  instances: [],
  favorites: ["ema", "rsi", "macd"],
  search: "",
  panelOpen: false,
  menuOpen: false,
  toggleFlag: (key) => {
    set((s) => {
      const flags = { ...s.flags, [key]: !s.flags[key] };
      // Sync pane flags to instances
      if (key === "rsi" && flags.rsi) {
        const has = s.instances.some((i) => i.pluginId === "rsi");
        if (!has) {
          return {
            flags,
            instances: [
              ...s.instances,
              {
                instanceId: uid("ind-"),
                pluginId: "rsi",
                settings: { ...getIndicatorPlugin("rsi")!.meta.defaultSettings },
              },
            ],
          };
        }
      }
      if (key === "macd" && flags.macd) {
        const has = s.instances.some((i) => i.pluginId === "macd");
        if (!has) {
          return {
            flags,
            instances: [
              ...s.instances,
              {
                instanceId: uid("ind-"),
                pluginId: "macd",
                settings: { ...getIndicatorPlugin("macd")!.meta.defaultSettings },
              },
            ],
          };
        }
      }
      return { flags };
    });
  },
  setFlags: (flags) => set({ flags }),
  setMenuOpen: (menuOpen) => set({ menuOpen }),
  setPanelOpen: (panelOpen) => set({ panelOpen }),
  setSearch: (search) => set({ search }),
  addInstance: (pluginId) => {
    const plugin = getIndicatorPlugin(pluginId);
    if (!plugin) return;
    set((s) => ({
      instances: [
        ...s.instances,
        {
          instanceId: uid("ind-"),
          pluginId,
          settings: { ...plugin.meta.defaultSettings },
        },
      ],
      flags: {
        ...s.flags,
        ...(pluginId === "rsi" ? { rsi: true } : {}),
        ...(pluginId === "macd" ? { macd: true } : {}),
        ...(pluginId === "volume" ? { volume: true } : {}),
      },
    }));
  },
  removeInstance: (instanceId) =>
    set((s) => ({
      instances: s.instances.filter((i) => i.instanceId !== instanceId),
    })),
  duplicateInstance: (instanceId) =>
    set((s) => {
      const src = s.instances.find((i) => i.instanceId === instanceId);
      if (!src) return s;
      return {
        instances: [
          ...s.instances,
          { ...src, instanceId: uid("ind-"), settings: { ...src.settings } },
        ],
      };
    }),
  updateInstance: (instanceId, settings) =>
    set((s) => ({
      instances: s.instances.map((i) =>
        i.instanceId === instanceId
          ? { ...i, settings: { ...i.settings, ...settings } }
          : i,
      ),
    })),
  toggleFavorite: (pluginId) =>
    set((s) => ({
      favorites: s.favorites.includes(pluginId)
        ? s.favorites.filter((f) => f !== pluginId)
        : [...s.favorites, pluginId],
    })),
  setInstances: (instances) => set({ instances }),
}));

export { listIndicatorPlugins };
