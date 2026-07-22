export const DEFAULT_SYMBOL = "XAUUSD";
export const DEFAULT_TIMEFRAME = "M5";

export const MARKET_SYMBOLS = [
  "XAUUSD",
  "XAGUSD",
  "EURUSD",
  "GBPUSD",
  "USDJPY",
  "AUDUSD",
  "USDCAD",
  "NZDUSD",
  "USDCHF",
  "EURJPY",
  "GBPJPY",
  "EURGBP",
] as const;

export type MarketSymbol = (typeof MARKET_SYMBOLS)[number];

export const MARKET_CATEGORIES = {
  metals: ["XAUUSD", "XAGUSD"],
  forex: [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "NZDUSD",
    "USDCHF",
    "EURJPY",
    "GBPJPY",
    "EURGBP",
  ],
} as const;

export const TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"] as const;

export function symbolCategory(symbol: string): "metals" | "forex" | "other" {
  const upper = symbol.toUpperCase();
  if ((MARKET_CATEGORIES.metals as readonly string[]).includes(upper)) return "metals";
  if ((MARKET_CATEGORIES.forex as readonly string[]).includes(upper)) return "forex";
  return "other";
}

export function priceDigitsFor(symbol: string, price = 0): number {
  const upper = symbol.toUpperCase();
  if (upper.includes("JPY")) return 3;
  if (upper.startsWith("XAU") || upper.startsWith("XAG") || price >= 100) return 2;
  return 5;
}
