import { create } from "zustand";

interface SessionState {
  enabled: boolean;
  flags: Record<string, boolean>;
  setEnabled: (v: boolean) => void;
  toggle: (id: string) => void;
  setFlags: (flags: Record<string, boolean>) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  enabled: false,
  flags: { sydney: true, tokyo: true, london: true, newyork: true },
  setEnabled: (enabled) => set({ enabled }),
  toggle: (id) =>
    set((s) => ({ flags: { ...s.flags, [id]: !s.flags[id] } })),
  setFlags: (flags) => set({ flags }),
}));
