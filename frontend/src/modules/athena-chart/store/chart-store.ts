import { create } from "zustand";

interface ChartState {
  market: "forex" | "metals" | "crypto" | "indices";
  symbol: string;
  timeframe: string;
  loading: boolean;
  error: string | null;
  candleCount: number;
  setMarket: (market: ChartState["market"]) => void;
  setSymbol: (symbol: string) => void;
  setTimeframe: (timeframe: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setCandleCount: (n: number) => void;
}

export const useChartStore = create<ChartState>((set) => ({
  market: "metals",
  symbol: "XAUUSD",
  timeframe: "5M",
  loading: false,
  error: null,
  candleCount: 0,
  setMarket: (market) => set({ market }),
  setSymbol: (symbol) => set({ symbol: symbol.toUpperCase() }),
  setTimeframe: (timeframe) => set({ timeframe: timeframe.toUpperCase() }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setCandleCount: (candleCount) => set({ candleCount }),
}));
