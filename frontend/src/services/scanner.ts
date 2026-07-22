import { apiFetch } from "@/services/api-client";
import { normalizeSignal } from "@/lib/mappers";
import type { ScannerMeta, ScannerOpportunity } from "@/types";

export interface ScannerOpportunitiesResponse {
  opportunities: ScannerOpportunity[];
  groups?: {
    elite?: ScannerOpportunity[];
    high_quality?: ScannerOpportunity[];
    watchlist?: ScannerOpportunity[];
    no_trade?: ScannerOpportunity[];
  };
  meta: ScannerMeta;
}

export interface GetScannerOptions {
  timeframe: string;
  symbols?: string[];
  useWatchlist?: boolean;
  minScore?: number;
  signals?: string[];
  actionableOnly?: boolean;
  limit?: number;
}

function mapOpportunity(raw: Record<string, unknown>): ScannerOpportunity {
  const breakdownRaw = (raw.score_breakdown ?? raw.scoreBreakdown) as
    | Record<string, unknown>
    | undefined;
  return {
    id: String(raw.id ?? `${raw.symbol}-${raw.timeframe}`),
    symbol: String(raw.symbol ?? "").toUpperCase(),
    timeframe: String(raw.timeframe ?? "M15").toUpperCase(),
    signal: normalizeSignal(raw.signal),
    score: Math.round(Number(raw.score ?? 0)),
    confidence: Math.round(Number(raw.confidence ?? 0)),
    scoreBreakdown: breakdownRaw
      ? {
          base: Number(breakdownRaw.base ?? 0),
          quality: Number(breakdownRaw.quality ?? 0),
          probability: Number(breakdownRaw.probability ?? 0),
          confluence: Number(breakdownRaw.confluence ?? 0),
          momentumAlign: Number(
            breakdownRaw.momentum_align ?? breakdownRaw.momentumAlign ?? 0,
          ),
          freshness: Number(breakdownRaw.freshness ?? 0),
          session: Number(breakdownRaw.session ?? 0),
          marketWatch: Number(
            breakdownRaw.market_watch ?? breakdownRaw.marketWatch ?? 0,
          ),
          penalties: Number(breakdownRaw.penalties ?? 0),
        }
      : undefined,
    price: raw.price != null ? Number(raw.price) : undefined,
    changePercent:
      raw.change_percent != null
        ? Number(raw.change_percent)
        : raw.changePercent != null
          ? Number(raw.changePercent)
          : undefined,
    entry: raw.entry != null ? Number(raw.entry) : undefined,
    stopLoss:
      raw.stop_loss != null
        ? Number(raw.stop_loss)
        : raw.stopLoss != null
          ? Number(raw.stopLoss)
          : undefined,
    takeProfit:
      raw.take_profit != null
        ? Number(raw.take_profit)
        : raw.takeProfit != null
          ? Number(raw.takeProfit)
          : undefined,
    riskReward:
      raw.risk_reward != null
        ? Number(raw.risk_reward)
        : raw.riskReward != null
          ? Number(raw.riskReward)
          : undefined,
    trend: raw.trend != null ? String(raw.trend) : undefined,
    confluence: raw.confluence != null ? Number(raw.confluence) : undefined,
    tradeQuality:
      raw.trade_quality != null
        ? Number(raw.trade_quality)
        : raw.tradeQuality != null
          ? Number(raw.tradeQuality)
          : undefined,
    tradeProbability:
      raw.trade_probability != null
        ? Number(raw.trade_probability)
        : raw.tradeProbability != null
          ? Number(raw.tradeProbability)
          : undefined,
    setupQuality:
      raw.setup_quality != null
        ? Number(raw.setup_quality)
        : raw.setupQuality != null
          ? Number(raw.setupQuality)
          : undefined,
    setupQualityGrade:
      raw.setup_quality_grade != null
        ? String(raw.setup_quality_grade)
        : raw.setupQualityGrade != null
          ? String(raw.setupQualityGrade)
          : undefined,
    scannerGroup:
      raw.scanner_group != null
        ? String(raw.scanner_group)
        : raw.scannerGroup != null
          ? String(raw.scannerGroup)
          : undefined,
    rejectionChecklist: Array.isArray(raw.rejection_checklist)
      ? (raw.rejection_checklist as Array<Record<string, unknown>>).map((item) => ({
          name: String(item.name ?? "Check"),
          passed: Boolean(item.passed),
          detail: item.detail != null ? String(item.detail) : undefined,
          mandatory: item.mandatory != null ? Boolean(item.mandatory) : undefined,
        }))
      : Array.isArray(raw.rejectionChecklist)
        ? (raw.rejectionChecklist as Array<Record<string, unknown>>).map((item) => ({
            name: String(item.name ?? "Check"),
            passed: Boolean(item.passed),
            detail: item.detail != null ? String(item.detail) : undefined,
            mandatory: item.mandatory != null ? Boolean(item.mandatory) : undefined,
          }))
        : undefined,
    lifecycleState:
      raw.lifecycle_state != null
        ? String(raw.lifecycle_state)
        : raw.lifecycleState != null
          ? String(raw.lifecycleState)
          : undefined,
    correlated: Boolean(raw.correlated),
    correlationNote:
      raw.correlation_note != null
        ? String(raw.correlation_note)
        : raw.correlationNote != null
          ? String(raw.correlationNote)
          : undefined,
    session: String(raw.session ?? "London") as ScannerOpportunity["session"],
    reasons: Array.isArray(raw.reasons)
      ? (raw.reasons as unknown[]).map(String)
      : raw.reason
        ? [String(raw.reason)]
        : [],
    reason: Array.isArray(raw.reasons)
      ? (raw.reasons as unknown[]).map(String).slice(0, 2).join(" · ")
      : raw.reason
        ? String(raw.reason)
        : "",
    marketWatchTag:
      raw.market_watch_tag != null
        ? String(raw.market_watch_tag)
        : raw.marketWatchTag != null
          ? String(raw.marketWatchTag)
          : undefined,
    alsoHotOn: Array.isArray(raw.also_hot_on)
      ? (raw.also_hot_on as unknown[]).map(String)
      : Array.isArray(raw.alsoHotOn)
        ? (raw.alsoHotOn as unknown[]).map(String)
        : [],
    updatedAt:
      raw.updated_at != null
        ? String(raw.updated_at)
        : raw.updatedAt != null
          ? String(raw.updatedAt)
          : undefined,
    stalenessMs:
      raw.staleness_ms != null
        ? Number(raw.staleness_ms)
        : raw.stalenessMs != null
          ? Number(raw.stalenessMs)
          : undefined,
    stale: Boolean(raw.stale),
    recommendationId:
      raw.recommendation_id != null
        ? Number(raw.recommendation_id)
        : raw.recommendationId != null
          ? Number(raw.recommendationId)
          : undefined,
  };
}

function mapMeta(raw: Record<string, unknown>, timeframe: string): ScannerMeta {
  return {
    timeframe: String(raw.timeframe ?? timeframe),
    universeSize: Number(raw.universe_size ?? raw.universeSize ?? 0),
    opportunityCount: Number(
      raw.opportunity_count ?? raw.opportunityCount ?? 0,
    ),
    generatedAt: String(raw.generated_at ?? raw.generatedAt ?? new Date().toISOString()),
    lastMarketWatchScanAt:
      raw.last_market_watch_scan_at != null
        ? String(raw.last_market_watch_scan_at)
        : raw.lastMarketWatchScanAt != null
          ? String(raw.lastMarketWatchScanAt)
          : null,
    lastMarketWatchScanAgeMs:
      raw.last_market_watch_scan_age_ms != null
        ? Number(raw.last_market_watch_scan_age_ms)
        : raw.lastMarketWatchScanAgeMs != null
          ? Number(raw.lastMarketWatchScanAgeMs)
          : null,
    staleThresholdMinutes: Number(
      raw.stale_threshold_minutes ?? raw.staleThresholdMinutes ?? 45,
    ),
    symbolsScanned: Array.isArray(raw.symbols_scanned)
      ? (raw.symbols_scanned as unknown[]).map(String)
      : Array.isArray(raw.symbolsScanned)
        ? (raw.symbolsScanned as unknown[]).map(String)
        : [],
    groupCounts: (() => {
      const gc = (raw.group_counts ?? raw.groupCounts) as
        | Record<string, unknown>
        | undefined;
      if (!gc) return undefined;
      return {
        elite: Number(gc.elite ?? 0),
        highQuality: Number(gc.high_quality ?? gc.highQuality ?? 0),
        watchlist: Number(gc.watchlist ?? 0),
        noTrade: Number(gc.no_trade ?? gc.noTrade ?? 0),
      };
    })(),
  };
}

export async function getScannerOpportunities(
  options: GetScannerOptions,
): Promise<ScannerOpportunitiesResponse> {
  const params = new URLSearchParams({
    timeframe: options.timeframe,
  });
  if (options.symbols?.length) {
    params.set("symbols", options.symbols.join(","));
  }
  if (options.useWatchlist) {
    params.set("use_watchlist", "true");
  }
  if (options.minScore != null) {
    params.set("min_score", String(options.minScore));
  }
  if (options.signals?.length) {
    params.set("signals", options.signals.join(","));
  }
  if (options.actionableOnly) {
    params.set("actionable_only", "true");
  }
  if (options.limit != null) {
    params.set("limit", String(options.limit));
  }

  const raw = await apiFetch<Record<string, unknown>>(
    `/scanner/opportunities?${params.toString()}`,
  );
  const list = Array.isArray(raw.opportunities)
    ? (raw.opportunities as Record<string, unknown>[])
    : [];
  const metaRaw =
    raw.meta && typeof raw.meta === "object"
      ? (raw.meta as Record<string, unknown>)
      : {};

  return {
    opportunities: list.map(mapOpportunity),
    groups: (() => {
      const rawGroups = (raw.groups ?? {}) as Record<string, unknown>;
      const mapList = (key: string) =>
        Array.isArray(rawGroups[key])
          ? (rawGroups[key] as Record<string, unknown>[]).map(mapOpportunity)
          : undefined;
      return {
        elite: mapList("elite"),
        high_quality: mapList("high_quality"),
        watchlist: mapList("watchlist"),
        no_trade: mapList("no_trade"),
      };
    })(),
    meta: mapMeta(metaRaw, options.timeframe),
  };
}
