import { apiFetch } from "@/services/api-client";
import { mapRecommendation, mapTradeComparison, normalizeSignal, normalizeTrend, toNumber } from "@/lib/mappers";
import type {
  Recommendation,
  SimilarRecommendation,
  SymbolScenario,
  TimeframeSignalSnapshot,
  TradeComparison,
} from "@/types";

export async function getLatestRecommendation(
  symbol: string,
  timeframe?: string | null,
): Promise<Recommendation | null> {
  try {
    const params = new URLSearchParams({
      symbol,
    });
    if (timeframe) {
      params.set("timeframe", timeframe);
    }
    const raw = await apiFetch<Record<string, unknown> | null>(
      `/recommendations/latest?${params.toString()}`,
    );
    return mapRecommendation(raw ?? undefined, {
      symbol,
      timeframe: timeframe ?? undefined,
    });
  } catch {
    return null;
  }
}

function mapTimeframeSnapshot(
  raw: Record<string, unknown>,
): TimeframeSignalSnapshot {
  return {
    timeframe: String(raw.timeframe ?? "").toUpperCase(),
    signal: normalizeSignal(raw.signal),
    confidence: Math.round(toNumber(raw.confidence)),
    trend: normalizeTrend(raw.trend),
    confluence: Math.round(toNumber(raw.confluence)),
    recommendationId:
      raw.recommendation_id != null
        ? Number(raw.recommendation_id)
        : raw.recommendationId != null
          ? Number(raw.recommendationId)
          : null,
    createdAt:
      raw.created_at != null
        ? String(raw.created_at)
        : raw.createdAt != null
          ? String(raw.createdAt)
          : null,
  };
}

export async function getSymbolScenario(
  symbol: string,
): Promise<SymbolScenario | null> {
  try {
    const raw = await apiFetch<Record<string, unknown>>(
      `/recommendations/scenario?symbol=${encodeURIComponent(symbol)}`,
    );
    const bestRaw =
      raw.best && typeof raw.best === "object"
        ? (raw.best as Record<string, unknown>)
        : null;
    const byTfRaw = Array.isArray(raw.by_timeframe)
      ? (raw.by_timeframe as Record<string, unknown>[])
      : Array.isArray(raw.byTimeframe)
        ? (raw.byTimeframe as Record<string, unknown>[])
        : [];
    return {
      symbol: String(raw.symbol ?? symbol).toUpperCase(),
      best: mapRecommendation(bestRaw ?? undefined, { symbol }),
      byTimeframe: byTfRaw.map(mapTimeframeSnapshot),
    };
  } catch {
    return null;
  }
}

export async function getRecommendationHistory(
  symbol: string | null | undefined,
  timeframe?: string | null,
  limit = 20,
): Promise<Recommendation[]> {
  const params = new URLSearchParams({
    limit: String(limit),
  });
  if (timeframe) {
    params.set("timeframe", timeframe);
  }
  if (symbol && symbol.toUpperCase() !== "ALL") {
    params.set("symbol", symbol);
  }
  const raw = await apiFetch<Record<string, unknown>[]>(
    `/recommendations/history?${params.toString()}`,
  );
  return raw
    .map((item) =>
      mapRecommendation(item, {
        symbol: String(item.symbol ?? symbol ?? ""),
        timeframe: String(item.timeframe ?? timeframe ?? ""),
      }),
    )
    .filter((item): item is Recommendation => item !== null);
}

export async function getRecommendationById(
  id: string | number,
): Promise<Recommendation | null> {
  try {
    const raw = await apiFetch<Record<string, unknown>>(
      `/recommendations/${encodeURIComponent(String(id))}`,
    );
    return mapRecommendation(raw);
  } catch {
    return null;
  }
}

export async function getSimilarRecommendations(
  id: string | number,
  limit = 20,
): Promise<SimilarRecommendation[]> {
  const raw = await apiFetch<Record<string, unknown>[]>(
    `/recommendations/${encodeURIComponent(String(id))}/similar?limit=${limit}`,
  );
  return (raw ?? []).map((item) => ({
    id: Number(item.id),
    symbol: String(item.symbol ?? ""),
    timeframe: String(item.timeframe ?? ""),
    signal: String(item.signal ?? ""),
    confidence: Number(item.confidence ?? 0),
    trend: String(item.trend ?? ""),
    riskReward: Number(item.risk_reward ?? item.riskReward ?? 0),
    similarity: Number(item.similarity ?? 0),
    outcomeLabel:
      item.outcome_label != null
        ? String(item.outcome_label)
        : item.outcomeLabel != null
          ? String(item.outcomeLabel)
          : null,
    pnlProxy:
      item.pnl_proxy != null
        ? Number(item.pnl_proxy)
        : item.pnlProxy != null
          ? Number(item.pnlProxy)
          : null,
    tradeProbability:
      item.trade_probability != null
        ? Number(item.trade_probability)
        : item.tradeProbability != null
          ? Number(item.tradeProbability)
          : null,
    tradeQuality:
      item.trade_quality != null
        ? Number(item.trade_quality)
        : item.tradeQuality != null
          ? Number(item.tradeQuality)
          : null,
    qualityGrade:
      item.quality_grade != null
        ? String(item.quality_grade)
        : item.qualityGrade != null
          ? String(item.qualityGrade)
          : null,
    createdAt:
      item.created_at != null
        ? String(item.created_at)
        : item.createdAt != null
          ? String(item.createdAt)
          : null,
  }));
}

export async function compareRecommendations(
  id: string | number,
  otherId: string | number,
): Promise<TradeComparison | null> {
  const raw = await apiFetch<Record<string, unknown>>(
    `/recommendations/${encodeURIComponent(String(id))}/comparison/${encodeURIComponent(String(otherId))}`,
  );
  return mapTradeComparison(raw);
}

export async function analyzeMarket(
  symbol: string,
  timeframe: string,
): Promise<{ success: boolean; recommendation?: Recommendation; message?: string }> {
  // #region agent log
  const _dbgAccess = typeof window !== "undefined" ? localStorage.getItem("athena_access_token") : null;
  const _dbgRefresh = typeof window !== "undefined" ? localStorage.getItem("athena_refresh_token") : null;
  fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'77d2e9'},body:JSON.stringify({sessionId:'77d2e9',runId:'pre-fix',hypothesisId:'D',location:'recommendations.ts:analyzeMarket',message:'analyzeMarket called',data:{symbol,timeframe,hasAccess:Boolean(_dbgAccess),accessLen:_dbgAccess?.length??0,hasRefresh:Boolean(_dbgRefresh),origin:typeof window!=='undefined'?window.location.origin:null},timestamp:Date.now()})}).catch(()=>{});
  // #endregion
  const result = await apiFetch<{
    success: boolean;
    message?: string;
    recommendation?: Record<string, unknown>;
  }>(`/ai/analyze?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`, {
    method: "POST",
  });

  return {
    success: result.success,
    message: result.message,
    recommendation: mapRecommendation(result.recommendation, { symbol, timeframe }) ?? undefined,
  };
}
