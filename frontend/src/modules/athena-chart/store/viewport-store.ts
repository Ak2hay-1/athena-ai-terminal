import { create } from "zustand";
import type { ViewportState } from "../types";

interface ViewportStoreState extends ViewportState {
  setViewport: (state: ViewportState) => void;
}

export const useViewportStore = create<ViewportStoreState>((set) => ({
  from: 0,
  to: 100,
  setViewport: (state) => set(state),
}));
