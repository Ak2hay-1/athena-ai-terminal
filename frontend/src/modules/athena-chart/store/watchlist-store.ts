import { create } from "zustand";
import { MARKET_SYMBOLS } from "@/constants/markets";

export interface WatchlistItem {
  symbol: string;
  favorite: boolean;
  lastPrice: number;
  dailyPct: number;
  spread: number | null;
  spark: number[];
}

function mockItem(symbol: string, favorite = false): WatchlistItem {
  const base = symbol.startsWith("XAU") ? 2650 : symbol.includes("JPY") ? 150 : 1.08;
  const spark = Array.from({ length: 12 }, (_, i) => base * (1 + Math.sin(i) * 0.002));
  return {
    symbol,
    favorite,
    lastPrice: base,
    dailyPct: (Math.random() - 0.5) * 1.2,
    spread: null,
    spark,
  };
}

interface WatchlistState {
  items: WatchlistItem[];
  query: string;
  setQuery: (q: string) => void;
  toggleFavorite: (symbol: string) => void;
  reorder: (from: number, to: number) => void;
  addSymbol: (symbol: string) => void;
  removeSymbol: (symbol: string) => void;
  setItems: (items: WatchlistItem[]) => void;
}

const STORAGE_KEY = "athena.chart.watchlist.v1";

function load(): WatchlistItem[] {
  if (typeof window === "undefined") {
    return MARKET_SYMBOLS.slice(0, 8).map((s, i) => mockItem(s, i < 3));
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as WatchlistItem[];
  } catch {
    /* ignore */
  }
  return MARKET_SYMBOLS.slice(0, 8).map((s, i) => mockItem(s, i < 3));
}

export const useWatchlistStore = create<WatchlistState>((set, get) => ({
  items: load(),
  query: "",
  setQuery: (query) => set({ query }),
  toggleFavorite: (symbol) => {
    set((s) => ({
      items: s.items.map((i) =>
        i.symbol === symbol ? { ...i, favorite: !i.favorite } : i,
      ),
    }));
    persist(get().items);
  },
  reorder: (from, to) => {
    set((s) => {
      const items = s.items.slice();
      const [moved] = items.splice(from, 1);
      items.splice(to, 0, moved);
      return { items };
    });
    persist(get().items);
  },
  addSymbol: (symbol) => {
    const upper = symbol.toUpperCase();
    if (get().items.some((i) => i.symbol === upper)) return;
    set((s) => ({ items: [...s.items, mockItem(upper, true)] }));
    persist(get().items);
  },
  removeSymbol: (symbol) => {
    set((s) => ({ items: s.items.filter((i) => i.symbol !== symbol) }));
    persist(get().items);
  },
  setItems: (items) => {
    set({ items });
    persist(items);
  },
}));

function persist(items: WatchlistItem[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    /* ignore */
  }
}
