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
  timeframe: string;
  reasons: string[];
  confluence?: number;
  createdAt: string;
}

export interface WatchlistItem {
  symbol: string;
  price: number;
  changePercent: number;
  signal: Signal;
  confidence: number;
  trend: Trend;
  referencePrice?: number;
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

export interface ScannerOpportunity {
  id: string;
  symbol: string;
  signal: Signal;
  confidence: number;
  timeframe: string;
  session: MarketSession;
  reason: string;
  price?: number;
  changePercent?: number;
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
