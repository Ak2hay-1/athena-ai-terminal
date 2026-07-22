import { create } from "zustand";

/** Replay mode — placeholder for future playback engine. */
interface ReplayState {
  enabled: boolean;
  cursorIndex: number;
  speed: number;
  setEnabled: (enabled: boolean) => void;
  setCursorIndex: (index: number) => void;
  setSpeed: (speed: number) => void;
}

export const useReplayStore = create<ReplayState>((set) => ({
  enabled: false,
  cursorIndex: 0,
  speed: 1,
  setEnabled: (enabled) => set({ enabled }),
  setCursorIndex: (cursorIndex) => set({ cursorIndex }),
  setSpeed: (speed) => set({ speed }),
}));
