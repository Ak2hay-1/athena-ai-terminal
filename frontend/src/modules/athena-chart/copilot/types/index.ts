/**
 * Athena Copilot — types.
 * GPT explains/coaches from structured engine context only — never invents signals.
 */

export type CopilotTab =
  | "overview"
  | "analysis"
  | "chat"
  | "trade"
  | "journal"
  | "coach"
  | "history";

export type CopilotRole = "user" | "assistant" | "system";

export type QuickActionId =
  | "explain_chart"
  | "explain_trend"
  | "explain_structure"
  | "why_buy"
  | "why_sell"
  | "current_risks"
  | "find_better_entry"
  | "review_my_trade"
  | "summarize_session"
  | "detect_mistakes"
  | "generate_journal";

export type ExplainTargetKind =
  | "candle"
  | "order_block"
  | "trendline"
  | "fvg"
  | "liquidity"
  | "trade"
  | "structure"
  | "zone";

export type SummaryHorizon =
  | "1m"
  | "5m"
  | "1h"
  | "session"
  | "daily"
  | "weekly";

export type AiProviderId = "azure" | "openai" | "local" | "mock";

export interface CopilotMessage {
  id: string;
  role: CopilotRole;
  content: string;
  createdAt: number;
  pinned?: boolean;
  meta?: {
    action?: QuickActionId | "click_explain" | "qa" | "summary" | "coach" | "review";
    provider?: AiProviderId;
    model?: string;
    fromCache?: boolean;
  };
}

export interface ExplainTarget {
  kind: ExplainTargetKind;
  id?: string;
  label: string;
  price?: number;
  time?: string;
  extras?: Record<string, string | number | boolean | null>;
}

export interface ChartAwareness {
  symbol: string;
  timeframe: string;
  visibleFrom?: string;
  visibleTo?: string;
  selectedCandleTime?: string | null;
  hoverPrice?: number | null;
  selectedDrawingIds?: string[];
  openIndicators?: string[];
  zoomBars?: number | null;
  selectedTradeId?: string | null;
}

/** Compact structured context — never raw candle arrays. */
export interface AthenaStructuredContext {
  symbol: string;
  timeframe: string;
  trend: {
    classification: string;
    direction: string;
    confidence: number;
  };
  structure: {
    latestLabels: string[];
    bias: string;
  };
  liquidity: Array<{ kind: string; importance: number; price: number }>;
  orderBlocks: Array<{ bias: string; score: number; top: number; bottom: number }>;
  fvgs: Array<{ bias: string; status: string; fillRatio: number }>;
  volume: {
    participation: string;
    pressure: string;
    flags: string[];
  };
  sessions: Array<{ name: string; active: boolean; killZone: boolean }>;
  confluence: {
    bullish: number;
    bearish: number;
    neutral: number;
    confidence: number;
    drivers: string[];
  };
  opportunity: {
    bias: string;
    grade: string;
    confidence: number;
    confidenceLabel: string;
    probability: { bullish: number; bearish: number; neutral: number };
    direction: string;
    entry?: number;
    stopLoss?: number;
    takeProfit1?: number;
    takeProfit2?: number;
    takeProfit3?: number;
    riskReward?: number;
    riskCategory?: string;
    supporting: string[];
    opposing: string[];
    explanationSummary?: string;
    explanationReasons?: string[];
    explanationRisks?: string[];
    exitAction?: string;
    exitReason?: string;
    mtfAlignment?: number;
    mtfConflict?: number;
    mtfDominant?: string;
  } | null;
  indicators: {
    rsi?: number | null;
    macdHist?: number | null;
    vwapBias?: string | null;
    atr?: number | null;
  };
  awareness: ChartAwareness;
  selectedObject?: ExplainTarget | null;
  recentDecisions: string[];
  news?: Array<{ title: string; impact: string }>;
  positions?: Array<{ side: string; entry: number; sl?: number; tp?: number }>;
  journalNotes?: string[];
  preferences?: Record<string, string | number | boolean>;
  dataGaps: string[];
}

export interface PromptPacket {
  system: string;
  user: string;
  estimatedTokens: number;
  contextHash: string;
}

export interface AiCompletionRequest {
  messages: Array<{ role: CopilotRole; content: string }>;
  symbol?: string;
  timeframe?: string;
  maxTokens?: number;
  temperature?: number;
}

export interface AiCompletionResult {
  success: boolean;
  content: string;
  provider: AiProviderId;
  model: string;
  message?: string;
  fromCache?: boolean;
}

export interface CopilotSettings {
  provider: AiProviderId;
  autoSummarizeOnOpen: boolean;
  explainOnClick: boolean;
  minConfidenceDeltaForAuto: number;
  maxContextTokens: number;
}

export const DEFAULT_COPILOT_SETTINGS: CopilotSettings = {
  provider: "azure",
  autoSummarizeOnOpen: false,
  explainOnClick: true,
  minConfidenceDeltaForAuto: 8,
  maxContextTokens: 1800,
};

export interface ConversationKey {
  symbol: string;
  timeframe: string;
  tradeId?: string | null;
}

export interface ConversationThread {
  key: string;
  symbol: string;
  timeframe: string;
  tradeId?: string | null;
  messages: CopilotMessage[];
  updatedAt: number;
}
