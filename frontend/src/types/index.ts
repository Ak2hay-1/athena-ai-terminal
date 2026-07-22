export type Signal =
  | "STRONG_BUY"
  | "BUY"
  | "NEUTRAL"
  | "HOLD"
  | "NO_TRADE"
  | "SELL"
  | "STRONG_SELL";

export type Trend = "Bullish" | "Bearish" | "Neutral";
export type RiskLevel = "Low" | "Medium" | "High";
export type MarketSession =
  | "Sydney"
  | "Tokyo"
  | "London"
  | "New York"
  | "Overlap";

export interface ConfidenceBreakdown {
  trend: number;
  momentum: number;
  structure: number;
  liquidity: number;
  news: number;
  risk: number;
  trendMax: number;
  momentumMax: number;
  structureMax: number;
  liquidityMax: number;
  newsMax: number;
  riskMax: number;
}

export interface ChecklistItem {
  name: string;
  passed: boolean;
}

export interface MarketHeatmap {
  trend: number;
  momentum: number;
  structure: number;
  liquidity: number;
  volatility: number;
  news: number;
  risk: number;
}

export interface EntryZone {
  aggressive: number;
  optimalLow: number;
  optimalHigh: number;
  conservative: number;
}

export interface TradeProbability {
  probability: number;
  confidenceCategory: string;
  similarTrades: number;
  historicalWinRate: number;
  expectedRr: number;
  expectedHoldTime: string;
  historicalAverageProfit: number;
  historicalAverageLoss: number;
}

export interface SimilarRecommendation {
  id: number;
  symbol: string;
  timeframe: string;
  signal: string;
  confidence: number;
  trend: string;
  riskReward: number;
  similarity: number;
  outcomeLabel?: string | null;
  pnlProxy?: number | null;
  tradeProbability?: number | null;
  tradeQuality?: number | null;
  qualityGrade?: string | null;
  createdAt?: string | null;
}

export interface MetricComparison {
  a: string | number | null;
  b: string | number | null;
  winner?: string | null;
}

export interface TradeComparison {
  winner: string;
  comparison: Record<string, MetricComparison>;
}

export interface Recommendation {
  id: string;
  symbol: string;
  signal: Signal;
  confidence: number;
  trend: Trend;
  risk: RiskLevel;
  entry: number;
  entryType?: string;
  stopLoss: number;
  takeProfit: number;
  riskReward: number;
  riskPips?: number;
  rewardPips?: number;
  slReason?: string;
  tpReason?: string;
  validation?: Record<string, boolean>;
  confidenceBreakdown?: ConfidenceBreakdown;
  checklist?: ChecklistItem[];
  heatmap?: MarketHeatmap;
  entryZone?: EntryZone;
  tradeProbability?: number;
  similarTradeCount?: number;
  historicalWinRate?: number;
  expectedRr?: number;
  expectedHoldTime?: string;
  tradeQuality?: number;
  qualityGrade?: string;
  historicalInsights?: string[];
  probabilityDetail?: TradeProbability;
  timeframe: string;
  reasons: string[];
  confluence?: number;
  createdAt: string;
}

/** Latest signal for one timeframe in the overall scenario strip. */
export interface TimeframeSignalSnapshot {
  timeframe: string;
  signal: Signal;
  confidence: number;
  trend: Trend;
  confluence: number;
  recommendationId?: number | null;
  createdAt?: string | null;
}

/** Best setup + per-TF snapshot for a symbol. */
export interface SymbolScenario {
  symbol: string;
  best: Recommendation | null;
  byTimeframe: TimeframeSignalSnapshot[];
}

export interface WatchlistItem {
  symbol: string;
  price: number;
  changePercent: number;
  signal: Signal;
  confidence: number;
  trend: Trend;
  referencePrice?: number;
  setupQuality?: number;
  scannerGroup?: string;
}

export interface Position {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  entry: number;
  stopLoss: number;
  takeProfit: number;
  volume: number;
  pnl: number;
  status: "open" | "closed";
}

export interface MarketStatus {
  session: MarketSession;
  volatility: "Low" | "Medium" | "High";
  marketOpen: boolean;
  marketReason: string;
  score: number;
  feedConnected: boolean;
  wsConnected: boolean;
}

export interface NewsHeadline {
  id: string;
  title: string;
  summary?: string;
  impact: "High" | "Medium" | "Low";
  time: string;
  publishedAt?: string;
  symbols: string[];
  sentimentScore?: number;
  source?: string;
}

export interface NewsContext {
  sentiment: string;
  score: number;
  confidence?: number;
  highImpactUpcoming: boolean;
  headlines: string[];
  reasons?: string[];
  upcomingEvents?: Array<{
    title: string;
    impact: "High" | "Medium" | "Low";
    publishedAt: string;
  }>;
}

export interface LearningStats {
  patternWinRates: Record<string, number>;
  weights: Record<string, number>;
  sampleSize: number;
  modelAccuracy: number | null;
}

export interface ActivityEvent {
  id: string;
  title: string;
  description: string;
  time: string;
  tone: "ai" | "market" | "system" | "trade";
}

export interface ScannerScoreBreakdown {
  base: number;
  quality: number;
  probability: number;
  confluence: number;
  momentumAlign: number;
  freshness: number;
  session: number;
  marketWatch: number;
  penalties: number;
}

export interface ScannerOpportunity {
  id: string;
  symbol: string;
  signal: Signal;
  /** Server scanner rank score (0–100). Prefer this over confidence for ranking. */
  score: number;
  /** Model confidence (not inflated by momentum). */
  confidence: number;
  scoreBreakdown?: ScannerScoreBreakdown;
  timeframe: string;
  session: MarketSession;
  reasons: string[];
  /** Legacy single-line reason for preview cards. */
  reason: string;
  price?: number;
  changePercent?: number;
  entry?: number;
  stopLoss?: number;
  takeProfit?: number;
  riskReward?: number;
  trend?: string;
  confluence?: number;
  tradeQuality?: number;
  tradeProbability?: number;
  setupQuality?: number;
  setupQualityGrade?: string;
  scannerGroup?: "elite" | "high_quality" | "watchlist" | "no_trade" | string;
  rejectionChecklist?: Array<{
    name: string;
    passed: boolean;
    detail?: string;
    mandatory?: boolean;
  }>;
  lifecycleState?: string;
  correlated?: boolean;
  correlationNote?: string;
  marketWatchTag?: string;
  alsoHotOn?: string[];
  updatedAt?: string;
  stalenessMs?: number;
  stale?: boolean;
  recommendationId?: number;
}

export interface ScannerGroupCounts {
  elite: number;
  highQuality: number;
  watchlist: number;
  noTrade: number;
}

export interface ScannerMeta {
  timeframe: string;
  universeSize: number;
  opportunityCount: number;
  generatedAt: string;
  lastMarketWatchScanAt?: string | null;
  lastMarketWatchScanAgeMs?: number | null;
  staleThresholdMinutes: number;
  symbolsScanned: string[];
  groupCounts?: ScannerGroupCounts;
}

export interface HealthStatus {
  status: string;
  database?: string;
  service?: string;
  version?: string;
}

export type UserRole = "ADMIN" | "TRADER" | "VIEWER";

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active?: boolean;
  is_verified?: boolean;
  is_superuser?: boolean;
  last_login?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface AdminOverview {
  health: {
    status: string;
    database: string;
    service: string;
    version: string;
  };
  mt5: {
    connected: boolean;
    initialized: boolean;
    logged_in: boolean;
    server?: string | null;
    login?: number | null;
    message: string;
  };
  learning: {
    enabled: boolean;
    min_samples: number;
    retrain_interval_hours: number;
    model_path: string;
  };
  users: {
    total: number;
    active: number;
    admins: number;
  };
  config: {
    app_env: string;
    execution_provider: string;
    market_symbols: string[];
    market_timeframes: string[];
    ai_provider: string;
    ai_model: string;
    ollama_model?: string;
    collector_interval_seconds: number;
  };
}

export interface LearningRetrainResult {
  symbol: string;
  timeframe: string;
  accuracy: number;
  sample_size: number;
}

export interface SchedulerJobStatus {
  id: string;
  name: string;
  next_run_time?: string | null;
  trigger: string;
}

export interface SchedulerStatus {
  name: string;
  running: boolean;
  jobs: SchedulerJobStatus[];
}

export interface AdminSchedulers {
  market: SchedulerStatus;
  news_learning: SchedulerStatus;
  timezone: string;
}

export interface SchedulerTriggerResult {
  triggered: string;
  next_run_time: string;
  timeframe?: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Candle {
  symbol: string;
  timeframe: string;
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  tick_volume: number;
}

export interface MarketQuote {
  symbol: string;
  bid: number;
  ask: number;
  mid: number;
  time?: string | null;
  source: "tick" | "candle" | string;
}
