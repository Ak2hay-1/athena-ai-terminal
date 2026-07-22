export function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

export function uid(prefix: string): string {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export function round(n: number, d = 2): number {
  const f = 10 ** d;
  return Math.round(n * f) / f;
}

export function weekKey(ts: number): string {
  const d = new Date(ts);
  const onejan = new Date(d.getFullYear(), 0, 1);
  const week = Math.ceil(((d.getTime() - onejan.getTime()) / 86400000 + onejan.getDay() + 1) / 7);
  return `${d.getFullYear()}-W${String(week).padStart(2, "0")}`;
}

export function dayKey(ts: number): string {
  return new Date(ts).toISOString().slice(0, 10);
}

export function winRate(wins: number, total: number): number {
  if (total <= 0) return 0;
  return round((wins / total) * 100, 1);
}

export function profitFactor(grossWin: number, grossLossAbs: number): number {
  if (grossLossAbs <= 0) return grossWin > 0 ? 99 : 0;
  return round(grossWin / grossLossAbs, 2);
}

export function expectancy(winRatePct: number, avgWin: number, avgLossAbs: number): number {
  const p = winRatePct / 100;
  return round(p * avgWin - (1 - p) * avgLossAbs, 3);
}

export function maxDrawdown(pnls: number[]): number {
  let peak = 0;
  let equity = 0;
  let maxDd = 0;
  for (const p of pnls) {
    equity += p;
    peak = Math.max(peak, equity);
    maxDd = Math.max(maxDd, peak - equity);
  }
  return round(maxDd, 2);
}

export function confidenceBucket(conf: number): { key: string; mid: number } {
  const lo = Math.floor(conf / 10) * 10;
  const hi = lo + 10;
  return { key: `${lo}-${hi}`, mid: lo + 5 };
}
