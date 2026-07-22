import type { IndicatorDefinition } from "../types";

export const AVAILABLE_INDICATORS: IndicatorDefinition[] = [
  { id: "ema20", label: "EMA 20", category: "overlay", defaultEnabled: false },
  { id: "ema50", label: "EMA 50", category: "overlay", defaultEnabled: false },
  { id: "sma20", label: "SMA 20", category: "overlay" },
  { id: "sma50", label: "SMA 50", category: "overlay" },
  { id: "sma200", label: "SMA 200", category: "overlay" },
  { id: "bollinger", label: "Bollinger Bands", category: "overlay" },
  { id: "vwap", label: "VWAP", category: "overlay" },
  { id: "atr", label: "ATR", category: "overlay" },
  { id: "rsi", label: "RSI", category: "pane" },
  { id: "macd", label: "MACD", category: "pane" },
  { id: "volume", label: "Volume", category: "pane", defaultEnabled: true },
  { id: "priceLine", label: "Last Price", category: "overlay", defaultEnabled: true },
];

export const indicatorService = {
  list: () => AVAILABLE_INDICATORS,
};
