export function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

export function roundPrice(n: number, digits = 5): number {
  const f = 10 ** digits;
  return Math.round(n * f) / f;
}

export function lastFinite(arr: Array<number | null | undefined>): number | null {
  for (let i = arr.length - 1; i >= 0; i--) {
    const v = arr[i];
    if (v != null && Number.isFinite(v)) return v;
  }
  return null;
}

export function normalizeProbabilities(
  bull: number,
  bear: number,
  neut: number,
): { bullish: number; bearish: number; neutral: number } {
  const b = Math.max(0, bull);
  const s = Math.max(0, bear);
  const n = Math.max(0, neut);
  const sum = b + s + n || 1;
  const bullish = Math.round((b / sum) * 1000) / 10;
  const bearish = Math.round((s / sum) * 1000) / 10;
  let neutral = Math.round((100 - bullish - bearish) * 10) / 10;
  if (neutral < 0) neutral = 0;
  const drift = Math.round((100 - bullish - bearish - neutral) * 10) / 10;
  return {
    bullish,
    bearish,
    neutral: Math.round((neutral + drift) * 10) / 10,
  };
}

export function uid(prefix: string): string {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

/** Deterministic id from parts — same inputs → same id. */
export function stableId(prefix: string, ...parts: Array<string | number>): string {
  const raw = parts.map((p) => String(p)).join("|");
  let h = 2166136261;
  for (let i = 0; i < raw.length; i++) {
    h ^= raw.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return `${prefix}_${(h >>> 0).toString(36)}`;
}
