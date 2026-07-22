import type {
  ChecklistItem,
  ConfidenceBreakdown,
  EntryZone,
  MarketHeatmap,
  MarketSession,
  Recommendation,
  RiskLevel,
  Signal,
  TradeComparison,
  TradeProbability,
  Trend,
} from "@/types";

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
  // London/NY overlap 12:00–16:00 UTC
  if (hour >= 12 && hour < 16) return "Overlap";
  // London 07:00–12:00 (overlap handled above)
  if (hour >= 7 && hour < 12) return "London";
  // New York 16:00–21:00
  if (hour >= 16 && hour < 21) return "New York";
  // Tokyo 00:00–07:00 (overlap with Sydney early hours labeled Tokyo)
  if (hour >= 0 && hour < 7) return "Tokyo";
  // Sydney 21:00–00:00
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
  const reasonsRaw = Array.isArray(raw.reason)
    ? (raw.reason as unknown[]).map(String)
    : Array.isArray(raw.reasoning)
      ? (raw.reasoning as unknown[]).map(String)
      : [];
  // Deduplicate while preserving order (API may store sl_reason twice via _from_plan)
  const reasons = [...new Set(reasonsRaw)];

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
    confidenceBreakdown: mapConfidenceBreakdown(
      (raw.confidence_breakdown ?? raw.confidenceBreakdown) as Record<string, unknown> | null | undefined,
    ),
    checklist: mapChecklist(
      (raw.institutional_checklist ?? raw.checklist ?? raw.institutionalChecklist) as unknown,
    ),
    heatmap: mapHeatmap(
      (raw.market_heatmap ?? raw.heatmap ?? raw.marketHeatmap) as Record<string, unknown> | null | undefined,
    ),
    entryZone: mapEntryZone(
      (raw.entry_zone ?? raw.entryZone) as Record<string, unknown> | null | undefined,
    ),
    tradeProbability:
      raw.trade_probability != null || raw.tradeProbability != null
        ? Math.round(toNumber(raw.trade_probability ?? raw.tradeProbability))
        : undefined,
    similarTradeCount:
      raw.similar_trade_count != null || raw.similarTradeCount != null
        ? Math.round(toNumber(raw.similar_trade_count ?? raw.similarTradeCount))
        : undefined,
    historicalWinRate:
      raw.historical_win_rate != null || raw.historicalWinRate != null
        ? Math.round(toNumber(raw.historical_win_rate ?? raw.historicalWinRate))
        : undefined,
    expectedRr:
      raw.expected_rr != null || raw.expectedRr != null
        ? toNumber(raw.expected_rr ?? raw.expectedRr)
        : undefined,
    expectedHoldTime:
      raw.expected_hold_time != null
        ? String(raw.expected_hold_time)
        : raw.expectedHoldTime != null
          ? String(raw.expectedHoldTime)
          : undefined,
    tradeQuality:
      raw.trade_quality != null || raw.tradeQuality != null
        ? Math.round(toNumber(raw.trade_quality ?? raw.tradeQuality))
        : undefined,
    qualityGrade:
      raw.quality_grade != null
        ? String(raw.quality_grade)
        : raw.qualityGrade != null
          ? String(raw.qualityGrade)
          : undefined,
    historicalInsights: Array.isArray(raw.historical_insights)
      ? (raw.historical_insights as unknown[]).map(String)
      : Array.isArray(raw.historicalInsights)
        ? (raw.historicalInsights as unknown[]).map(String)
        : undefined,
    probabilityDetail: mapTradeProbability(
      (raw.probability_detail ?? raw.probabilityDetail) as
        | Record<string, unknown>
        | null
        | undefined,
    ),
    timeframe: String(raw.timeframe ?? fallbacks?.timeframe ?? "M1").toUpperCase(),
    reasons,
    confluence:
      raw.confluence === undefined || raw.confluence === null
        ? undefined
        : Math.round(toNumber(raw.confluence)),
    createdAt: String(raw.created_at ?? raw.createdAt ?? new Date().toISOString()),
  };
}

export function mapTradeProbability(
  raw: Record<string, unknown> | null | undefined,
): TradeProbability | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const probability = Math.round(toNumber(raw.probability));
  if (probability <= 0 && toNumber(raw.similar_trades ?? raw.similarTrades) <= 0) {
    return undefined;
  }
  return {
    probability,
    confidenceCategory: String(
      raw.confidence_category ?? raw.confidenceCategory ?? "LOW_SAMPLE",
    ),
    similarTrades: Math.round(toNumber(raw.similar_trades ?? raw.similarTrades)),
    historicalWinRate: Math.round(
      toNumber(raw.historical_win_rate ?? raw.historicalWinRate),
    ),
    expectedRr: toNumber(raw.expected_rr ?? raw.expectedRr),
    expectedHoldTime: String(raw.expected_hold_time ?? raw.expectedHoldTime ?? ""),
    historicalAverageProfit: toNumber(
      raw.historical_average_profit ?? raw.historicalAverageProfit,
    ),
    historicalAverageLoss: toNumber(
      raw.historical_average_loss ?? raw.historicalAverageLoss,
    ),
  };
}

export function mapTradeComparison(
  raw: Record<string, unknown> | null | undefined,
): TradeComparison | null {
  if (!raw || typeof raw !== "object") return null;
  const comparisonRaw = (raw.comparison ?? {}) as Record<string, unknown>;
  const comparison: TradeComparison["comparison"] = {};
  for (const [key, value] of Object.entries(comparisonRaw)) {
    if (!value || typeof value !== "object") continue;
    const row = value as Record<string, unknown>;
    comparison[key] = {
      a: (row.a as string | number | null) ?? null,
      b: (row.b as string | number | null) ?? null,
      winner: row.winner != null ? String(row.winner) : null,
    };
  }
  return {
    winner: String(raw.winner ?? "TIE"),
    comparison,
  };
}

function mapConfidenceBreakdown(
  raw: Record<string, unknown> | null | undefined,
): ConfidenceBreakdown | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const trend = toNumber(raw.trend);
  const momentum = toNumber(raw.momentum);
  const structure = toNumber(raw.structure);
  const liquidity = toNumber(raw.liquidity);
  const news = toNumber(raw.news);
  const risk = toNumber(raw.risk);
  if (trend + momentum + structure + liquidity + news + risk <= 0) return undefined;
  return {
    trend,
    momentum,
    structure,
    liquidity,
    news,
    risk,
    trendMax: toNumber(raw.trend_max ?? raw.trendMax, 35),
    momentumMax: toNumber(raw.momentum_max ?? raw.momentumMax, 15),
    structureMax: toNumber(raw.structure_max ?? raw.structureMax, 20),
    liquidityMax: toNumber(raw.liquidity_max ?? raw.liquidityMax, 15),
    newsMax: toNumber(raw.news_max ?? raw.newsMax, 10),
    riskMax: toNumber(raw.risk_max ?? raw.riskMax, 5),
  };
}

function mapChecklist(raw: unknown): ChecklistItem[] | undefined {
  if (!Array.isArray(raw) || raw.length === 0) return undefined;
  return raw.map((item) => {
    const row = (item ?? {}) as Record<string, unknown>;
    return {
      name: String(row.name ?? ""),
      passed: Boolean(row.passed),
    };
  });
}

function mapHeatmap(
  raw: Record<string, unknown> | null | undefined,
): MarketHeatmap | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const heatmap: MarketHeatmap = {
    trend: toNumber(raw.trend),
    momentum: toNumber(raw.momentum),
    structure: toNumber(raw.structure),
    liquidity: toNumber(raw.liquidity),
    volatility: toNumber(raw.volatility),
    news: toNumber(raw.news),
    risk: toNumber(raw.risk),
  };
  if (Object.values(heatmap).every((v) => v === 0)) return undefined;
  return heatmap;
}

function mapEntryZone(
  raw: Record<string, unknown> | null | undefined,
): EntryZone | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const zone: EntryZone = {
    aggressive: toNumber(raw.aggressive),
    optimalLow: toNumber(raw.optimal_low ?? raw.optimalLow),
    optimalHigh: toNumber(raw.optimal_high ?? raw.optimalHigh),
    conservative: toNumber(raw.conservative),
  };
  if (Object.values(zone).every((v) => v === 0)) return undefined;
  return zone;
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
