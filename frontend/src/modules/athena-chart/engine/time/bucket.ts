/**
 * UTC timeframe bucket helpers.
 * All candle construction uses these — never browser local time.
 */

export const API_TF_MS: Record<string, number> = {
  M1: 60_000,
  M5: 300_000,
  M15: 900_000,
  M30: 1_800_000,
  H1: 3_600_000,
  H4: 14_400_000,
  D1: 86_400_000,
};

export const MAX_GAP_FILL_BARS = 2_000;

export function timeframeDurationMs(tf: string): number | null {
  const upper = tf.toUpperCase();
  if (API_TF_MS[upper] != null) return API_TF_MS[upper];
  // UI aliases
  const aliases: Record<string, string> = {
    "1M": "M1",
    "5M": "M5",
    "15M": "M15",
    "30M": "M30",
    "1H": "H1",
    "4H": "H4",
  };
  const mapped = aliases[upper];
  return mapped ? API_TF_MS[mapped] ?? null : null;
}

/** Floor epoch ms to the start of its UTC timeframe bucket. */
export function bucketStartUtcMs(timeUtcMs: number, tf: string): number {
  const dur = timeframeDurationMs(tf);
  if (dur == null || !Number.isFinite(timeUtcMs)) {
    throw new Error(`Unsupported timeframe for bucketing: ${tf}`);
  }
  // D1: align to UTC midnight
  if (tf.toUpperCase() === "D1") {
    const d = new Date(timeUtcMs);
    return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
  }
  return Math.floor(timeUtcMs / dur) * dur;
}

export function bucketEndUtcMs(timeUtcMs: number, tf: string): number {
  const dur = timeframeDurationMs(tf);
  if (dur == null) throw new Error(`Unsupported timeframe: ${tf}`);
  return bucketStartUtcMs(timeUtcMs, tf) + dur;
}

export function isSameBucket(
  aUtcMs: number,
  bUtcMs: number,
  tf: string,
): boolean {
  return bucketStartUtcMs(aUtcMs, tf) === bucketStartUtcMs(bUtcMs, tf);
}

export function nextBucketStartUtcMs(bucketStartMs: number, tf: string): number {
  const dur = timeframeDurationMs(tf);
  if (dur == null) throw new Error(`Unsupported timeframe: ${tf}`);
  if (tf.toUpperCase() === "D1") {
    return bucketStartMs + 86_400_000;
  }
  return bucketStartMs + dur;
}

export function isoFromUtcMs(ms: number): string {
  return new Date(ms).toISOString();
}

export function utcMsFromIso(iso: string): number {
  return new Date(iso).getTime();
}
