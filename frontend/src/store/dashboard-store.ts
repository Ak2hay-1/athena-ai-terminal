"use client";

import { create } from "zustand";
import { DEFAULT_SYMBOL, DEFAULT_TIMEFRAME } from "@/constants/markets";

interface DashboardState {
  symbol: string;
  timeframe: string;
  setSymbol: (symbol: string) => void;
  setTimeframe: (timeframe: string) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  symbol: DEFAULT_SYMBOL,
  timeframe: DEFAULT_TIMEFRAME,
  setSymbol: (symbol) => set({ symbol }),
  setTimeframe: (timeframe) => set({ timeframe }),
}));
