import type { Signal, Trend, RiskLevel, MarketSession, Recommendation } from "@/types";

export function toNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  return fallback;
}

export function normalizeSignal(value: unknown): Signal {
  const raw = String(value ?? "HOLD").toUpperCase().replace(/\s+/g, "_");
  if (raw === "STRONG_BUY" || raw === "BUY") return raw;
  if (raw === "STRONG_SELL" || raw === "SELL") return raw;
  if (raw === "NEUTRAL") return "NEUTRAL";
  if (raw === "NO_TRADE") return "NO_TRADE";
  return "HOLD";
}

export function normalizeTrend(value: unknown): Trend {
  const raw = String(value ?? "").toUpperCase();
  if (raw === "BULLISH") return "Bullish";
  if (raw === "BEARISH") return "Bearish";
  return "Neutral";
}

export function deriveRisk(confidence: number, riskReward: number): RiskLevel {
  if (confidence >= 80 && riskReward >= 2) return "Low";
  if (confidence < 60 || riskReward < 1.5) return "High";
  return "Medium";
}

export function currentSession(date = new Date()): MarketSession {
  const hour = date.getUTCHours();
  if (hour >= 12 && hour < 16) return "Overlap";
  if (hour >= 7 && hour < 16) return "London";
  if (hour >= 12 && hour < 21) return "New York";
  if (hour >= 0 && hour < 9) return "Tokyo";
  return "Sydney";
}

export function mapRecommendation(
  raw: Record<string, unknown> | null | undefined,
  fallbacks?: { symbol?: string; timeframe?: string },
): Recommendation | null {
  if (!raw) return null;

  const confidence = Math.round(toNumber(raw.confidence));
  const entry = toNumber(raw.entry ?? raw.entry_price);
  const stopLoss = toNumber(raw.stop_loss ?? raw.stopLoss);
  const takeProfit = toNumber(raw.take_profit ?? raw.takeProfit);
  const riskReward = toNumber(raw.risk_reward ?? raw.riskReward);
  const reasons = Array.isArray(raw.reason)
    ? (raw.reason as unknown[]).map(String)
    : Array.isArray(raw.reasoning)
      ? (raw.reasoning as unknown[]).map(String)
      : [];

  const validationRaw = raw.validation;
  const validation =
    validationRaw && typeof validationRaw === "object"
      ? (validationRaw as Record<string, boolean>)
      : undefined;

  return {
    id: String(raw.id ?? `${raw.symbol ?? fallbacks?.symbol ?? "SYM"}-${Date.now()}`),
    symbol: String(raw.symbol ?? fallbacks?.symbol ?? "XAUUSD").toUpperCase(),
    signal: normalizeSignal(raw.signal),
    confidence,
    trend: normalizeTrend(raw.trend),
    risk: deriveRisk(confidence, riskReward),
    entry,
    entryType: raw.entry_type != null ? String(raw.entry_type) : raw.entryType != null ? String(raw.entryType) : undefined,
    stopLoss,
    takeProfit,
    riskReward,
    riskPips: raw.risk_pips != null ? toNumber(raw.risk_pips) : raw.riskPips != null ? toNumber(raw.riskPips) : undefined,
    rewardPips: raw.reward_pips != null ? toNumber(raw.reward_pips) : raw.rewardPips != null ? toNumber(raw.rewardPips) : undefined,
    slReason: raw.sl_reason != null ? String(raw.sl_reason) : raw.slReason != null ? String(raw.slReason) : undefined,
    tpReason: raw.tp_reason != null ? String(raw.tp_reason) : raw.tpReason != null ? String(raw.tpReason) : undefined,
    validation,
    timeframe: String(raw.timeframe ?? fallbacks?.timeframe ?? "M1").toUpperCase(),
    reasons,
    confluence:
      raw.confluence === undefined || raw.confluence === null
        ? undefined
        : Math.round(toNumber(raw.confluence)),
    createdAt: String(raw.created_at ?? raw.createdAt ?? new Date().toISOString()),
  };
}

export function formatImpact(value: unknown): "High" | "Medium" | "Low" {
  const raw = String(value ?? "Medium").toLowerCase();
  if (raw.includes("high")) return "High";
  if (raw.includes("low")) return "Low";
  return "Medium";
}

export function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return iso;
  const deltaMs = Date.now() - then;
  const future = deltaMs < 0;
  const delta = Math.abs(deltaMs);
  const minutes = Math.floor(delta / 60_000);
  if (minutes < 1) return future ? "soon" : "just now";
  if (minutes < 60) return future ? `in ${minutes}m` : `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return future ? `in ${hours}h` : `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return future ? `in ${days}d` : `${days}d ago`;
}
