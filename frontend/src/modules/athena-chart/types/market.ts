/** OHLC candlestick — framework-agnostic chart series point. */
export interface Candlestick {
  symbol: string;
  timeframe: string;
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  tick_volume: number;
}

/** Real-time tick (future streaming). */
export interface Tick {
  symbol: string;
  time: string;
  bid: number;
  ask: number;
  mid: number;
}

/** Executed trade marker. */
export interface Trade {
  id: string;
  symbol: string;
  time: string;
  side: "buy" | "sell";
  price: number;
  quantity: number;
}

/** Volume bar aligned to a candle index / time. */
export interface VolumeBar {
  time: string;
  volume: number;
  buyVolume?: number;
  sellVolume?: number;
}

export interface IndicatorDefinition {
  id: string;
  label: string;
  category: "overlay" | "pane";
  defaultEnabled?: boolean;
}

export interface MarketSession {
  id: string;
  name: string;
  openUtcMinutes: number;
  closeUtcMinutes: number;
  timezone: string;
}
