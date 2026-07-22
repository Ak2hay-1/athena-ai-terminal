/**
 * Athena Decision Engine — types.
 * Deterministic, explainable trade intelligence (no GPT).
 */

import type { AnalysisSnapshot } from "../../intelligence/types";
import type { Candlestick } from "../../types";

export type OpportunityBias =
  | "strong_buy"
  | "buy"
  | "watch_buy"
  | "neutral"
  | "watch_sell"
  | "sell"
  | "strong_sell";

export type TradeGrade = "A+" | "A" | "B+" | "B" | "C" | "Avoid";

export type RiskCategory = "low" | "medium" | "high" | "extreme";

export type EntryStyle = "conservative" | "balanced" | "aggressive";

export type StrategyProfileId = "scalping" | "intraday" | "swing" | "position";

export type RiskProfileMode = "conservative" | "balanced" | "aggressive";

export type ExitAction =
  | "partial_exit"
  | "move_stop_loss"
  | "close_trade"
  | "hold";

export type ConfidenceLabel =
  | "very_low"
  | "low"
  | "moderate"
  | "high"
  | "very_high";

export type SignalSource =
  | "trend"
  | "bos"
  | "choch"
  | "swing_structure"
  | "order_block"
  | "supply_demand"
  | "fvg"
  | "liquidity"
  | "volume"
  | "rsi"
  | "macd"
  | "vwap"
  | "atr"
  | "session"
  | "pattern"
  | "support_resistance";

export interface SignalWeights {
  trend: number;
  bos: number;
  choch: number;
  swing_structure: number;
  order_block: number;
  supply_demand: number;
  fvg: number;
  liquidity: number;
  volume: number;
  rsi: number;
  macd: number;
  vwap: number;
  atr: number;
  session: number;
  pattern: number;
  support_resistance: number;
}

export const DEFAULT_SIGNAL_WEIGHTS: SignalWeights = {
  trend: 20,
  bos: 14,
  choch: 16,
  swing_structure: 10,
  order_block: 18,
  supply_demand: 14,
  fvg: 14,
  liquidity: 16,
  volume: 12,
  rsi: 8,
  macd: 8,
  vwap: 7,
  atr: 5,
  session: 6,
  pattern: 10,
  support_resistance: 9,
};

export interface DecisionOverlayVisibility {
  buyZone: boolean;
  sellZone: boolean;
  entry: boolean;
  stopLoss: boolean;
  takeProfits: boolean;
  probabilityBadge: boolean;
  confidenceBadge: boolean;
  riskBadge: boolean;
  gradeBadge: boolean;
}

export const DEFAULT_DECISION_OVERLAYS: DecisionOverlayVisibility = {
  buyZone: true,
  sellZone: true,
  entry: true,
  stopLoss: true,
  takeProfits: true,
  probabilityBadge: true,
  confidenceBadge: true,
  riskBadge: true,
  gradeBadge: true,
};

export interface DecisionSettings {
  minConfidence: number;
  minRiskReward: number;
  strategy: StrategyProfileId;
  riskMode: RiskProfileMode;
  entryStyle: EntryStyle;
  signalWeights: SignalWeights;
  overlays: DecisionOverlayVisibility;
  accountRiskPct: number;
  accountEquity: number;
}

export const DEFAULT_DECISION_SETTINGS: DecisionSettings = {
  minConfidence: 55,
  minRiskReward: 1.5,
  strategy: "intraday",
  riskMode: "balanced",
  entryStyle: "balanced",
  signalWeights: { ...DEFAULT_SIGNAL_WEIGHTS },
  overlays: { ...DEFAULT_DECISION_OVERLAYS },
  accountRiskPct: 1,
  accountEquity: 10_000,
};

export interface NormalizedSignal {
  id: string;
  source: SignalSource;
  bias: "bullish" | "bearish" | "neutral";
  strength: number; // 0-100
  weight: number;
  weightedScore: number;
  label: string;
  supporting: boolean;
  ruleId: string;
  candleIndices: number[];
}

export interface ConfidenceResult {
  score: number;
  label: ConfidenceLabel;
  factors: {
    trendAgreement: number;
    timeframeAgreement: number;
    volumeConfirmation: number;
    liquidityConfirmation: number;
    patternConfirmation: number;
    momentumConfirmation: number;
    volatility: number;
    risk: number;
  };
}

export interface ProbabilityModel {
  bullish: number;
  bearish: number;
  neutral: number;
}

export interface EntryPlan {
  style: EntryStyle;
  entry: number;
  stopLoss: number;
  takeProfit1: number;
  takeProfit2: number;
  takeProfit3: number;
  riskReward: number;
  atrDistance: number;
  maximumRisk: number;
}

export interface ExitRecommendation {
  action: ExitAction;
  reason: string;
  suggestedStop?: number;
  partialPct?: number;
}

export interface RiskAssessment {
  maximumRisk: number;
  expectedDrawdown: number;
  positionSize: number;
  atrRisk: number;
  recommendedLeverage: number;
  expectedHoldingBars: number;
  category: RiskCategory;
}

export interface MtfVote {
  timeframe: string;
  bias: "bullish" | "bearish" | "neutral";
  confidence: number;
}

export interface MtfVotingResult {
  votes: MtfVote[];
  alignmentScore: number;
  conflictScore: number;
  dominantBias: "bullish" | "bearish" | "neutral";
}

export interface TradeOpportunity {
  id: string;
  symbol: string;
  timeframe: string;
  bias: OpportunityBias;
  direction: "long" | "short" | "flat";
  confidence: ConfidenceResult;
  qualityScore: number;
  grade: TradeGrade;
  probability: ProbabilityModel;
  entries: EntryPlan[];
  activeEntry: EntryPlan;
  risk: RiskAssessment;
  exit: ExitRecommendation;
  mtf: MtfVotingResult;
  supportingSignals: NormalizedSignal[];
  opposingSignals: NormalizedSignal[];
  buyZone: { top: number; bottom: number } | null;
  sellZone: { top: number; bottom: number } | null;
  explanation: ExplanationObject;
  expiresAt: number;
  createdAt: number;
  updatedAt: number;
  status: "active" | "expired" | "cancelled" | "tp1" | "tp2" | "tp3" | "stopped" | "closed";
}

export interface ExplanationObject {
  summary: string;
  reasons: string[];
  risks: string[];
  ruleIds: string[];
}

export interface DecisionEvent {
  id: string;
  time: string;
  timeSec: number;
  label: string;
  kind:
    | "opportunity"
    | "confidence_change"
    | "tp_reached"
    | "sl_move"
    | "close"
    | "cancel"
    | "update";
  confidence?: number;
  grade?: TradeGrade;
  bias?: "bullish" | "bearish" | "neutral";
  opportunityId?: string;
  meta?: Record<string, string | number | boolean>;
}

export interface DecisionMemoryRecord {
  id: string;
  at: number;
  type:
    | "opportunity_created"
    | "opportunity_updated"
    | "opportunity_cancelled"
    | "tp_hit"
    | "sl_hit"
    | "confidence_change"
    | "exit_action";
  opportunityId: string;
  payload: Record<string, unknown>;
}

export interface DecisionSnapshot {
  symbol: string;
  timeframe: string;
  opportunity: TradeOpportunity | null;
  signals: NormalizedSignal[];
  events: DecisionEvent[];
  analyzedAt: number;
  inputHash: string;
}

export interface DecisionInput {
  candles: Candlestick[];
  symbol: string;
  timeframe: string;
  analysis: AnalysisSnapshot;
  settings: DecisionSettings;
  /** Previous opportunity for incremental exit monitoring */
  previousOpportunity?: TradeOpportunity | null;
}
