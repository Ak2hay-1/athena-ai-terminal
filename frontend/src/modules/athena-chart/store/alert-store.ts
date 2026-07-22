import { create } from "zustand";
import { uid } from "../utils/uid";

export type AlertKind =
  | "price"
  | "trendline"
  | "indicator"
  | "cross"
  | "time";

export interface ChartAlert {
  id: string;
  kind: AlertKind;
  symbol: string;
  label: string;
  payload: Record<string, unknown>;
  enabled: boolean;
  createdAt: number;
}

/** Alerts architecture only — no backend firing. */
interface AlertState {
  alerts: ChartAlert[];
  draftOpen: boolean;
  setDraftOpen: (v: boolean) => void;
  addAlert: (partial: Omit<ChartAlert, "id" | "createdAt" | "enabled">) => void;
  removeAlert: (id: string) => void;
  toggleAlert: (id: string) => void;
}

export const useAlertStore = create<AlertState>((set) => ({
  alerts: [],
  draftOpen: false,
  setDraftOpen: (draftOpen) => set({ draftOpen }),
  addAlert: (partial) =>
    set((s) => ({
      alerts: [
        ...s.alerts,
        {
          ...partial,
          id: uid("alert-"),
          enabled: true,
          createdAt: Date.now(),
        },
      ],
    })),
  removeAlert: (id) =>
    set((s) => ({ alerts: s.alerts.filter((a) => a.id !== id) })),
  toggleAlert: (id) =>
    set((s) => ({
      alerts: s.alerts.map((a) =>
        a.id === id ? { ...a, enabled: !a.enabled } : a,
      ),
    })),
}));
