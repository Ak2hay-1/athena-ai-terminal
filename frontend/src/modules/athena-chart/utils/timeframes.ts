/** Extended chart timeframes including seconds and higher aggregations. */
export const CHART_TIMEFRAMES = [
  "1S",
  "5S",
  "15S",
  "30S",
  "1M",
  "2M",
  "3M",
  "5M",
  "15M",
  "30M",
  "1H",
  "2H",
  "4H",
  "6H",
  "8H",
  "12H",
  "D1",
  "W1",
  "MN1",
] as const;

export type ChartTimeframe = (typeof CHART_TIMEFRAMES)[number];

/** Minutes (fractional for seconds) per bar. */
export const TF_MINUTES: Record<string, number> = {
  "1S": 1 / 60,
  "5S": 5 / 60,
  "15S": 15 / 60,
  "30S": 30 / 60,
  "1M": 1,
  M1: 1,
  "2M": 2,
  "3M": 3,
  "5M": 5,
  M5: 5,
  "15M": 15,
  M15: 15,
  "30M": 30,
  M30: 30,
  "1H": 60,
  H1: 60,
  "2H": 120,
  "4H": 240,
  H4: 240,
  "6H": 360,
  "8H": 480,
  "12H": 720,
  D1: 1440,
  W1: 10080,
  MN1: 43200,
};

export function normalizeTimeframe(tf: string): string {
  const map: Record<string, string> = {
    M1: "1M",
    M5: "5M",
    M15: "15M",
    M30: "30M",
    H1: "1H",
    H4: "4H",
  };
  return map[tf.toUpperCase()] ?? tf.toUpperCase();
}

/** UI chart labels that have live backend candle support. */
export const LIVE_CHART_TIMEFRAMES = [
  "1M",
  "5M",
  "15M",
  "30M",
  "1H",
  "4H",
  "D1",
] as const;

const UI_TO_API: Record<string, string> = {
  "1M": "M1",
  M1: "M1",
  "5M": "M5",
  M5: "M5",
  "15M": "M15",
  M15: "M15",
  "30M": "M30",
  M30: "M30",
  "1H": "H1",
  H1: "H1",
  "4H": "H4",
  H4: "H4",
  D1: "D1",
};

const API_TO_UI: Record<string, string> = {
  M1: "1M",
  M5: "5M",
  M15: "15M",
  M30: "30M",
  H1: "1H",
  H4: "4H",
  D1: "D1",
};

/** Convert chart UI timeframe (e.g. 5M) to backend API timeframe (e.g. M5). */
export function toApiTimeframe(tf: string): string | null {
  return UI_TO_API[tf.toUpperCase()] ?? null;
}

/** Convert backend API timeframe (e.g. M5) to chart UI timeframe (e.g. 5M). */
export function fromApiTimeframe(tf: string): string {
  const upper = tf.toUpperCase();
  return API_TO_UI[upper] ?? normalizeTimeframe(upper);
}

export function isLiveTimeframe(tf: string): boolean {
  return toApiTimeframe(tf) != null;
}
