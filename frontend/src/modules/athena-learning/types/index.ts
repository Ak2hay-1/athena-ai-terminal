/**
 * Athena Self-Learning Intelligence — types.
 * Deterministic, explainable, per-user isolated. No GPT retraining.
 */

export type StrategyKind = "scalping" | "intraday" | "swing" | "position";
export type RiskMode = "conservative" | "balanced" | "aggressive";
export type OutcomeLabel = "win" | "loss" | "breakeven" | "cancelled" | "unknown";
export type OutcomeResult =
  | "tp1"
  | "tp2"
  | "tp3"
  | "sl"
  | "manual_exit"
  | "timeout"
  | "cancelled";

export type BehaviorFlag =
  | "fomo"
  | "revenge_trading"
  | "overtrading"
  | "early_exit"
  | "late_exit"
  | "moving_stop_loss"
  | "cancelling_winners"
  | "holding_losers"
  | "skipping_good_trades"
  | "chasing_price";

export type LearningEventType =
  | "trade_opened"
  | "trade_closed"
  | "setup_recorded"
  | "confidence_logged"
  | "ai_recommendation"
  | "tp_hit"
  | "sl_hit"
  | "cancellation"
  | "manual_override"
  | "ignored_signal"
  | "behavior"
  | "mistake"
  | "prediction"
  | "weight_change"
  | "goal_progress"
  | "achievement";

export interface LearningEvent {
  id: string;
  at: number;
  userId: string;
  type: LearningEventType;
  symbol?: string;
  timeframe?: string;
  payload: Record<string, unknown>;
}

/** Immutable record of a completed (or cancelled) trade/setup for learning. */
export interface TradeLearningRecord {
  id: string;
  userId: string;
  symbol: string;
  timeframe: string;
  strategy: StrategyKind;
  riskMode: RiskMode;
  session?: string;
  direction: "long" | "short" | "flat";
  bias: string;
  grade?: string;
  confidenceAtEntry: number;
  probabilityBullish?: number;
  probabilityBearish?: number;
  entry: number;
  stopLoss: number;
  takeProfit1: number;
  takeProfit2?: number;
  takeProfit3?: number;
  plannedRr: number;
  openedAt: number;
  closedAt: number;
  outcome: OutcomeLabel;
  result: OutcomeResult;
  pnl: number;
  realizedRr: number;
  holdMinutes: number;
  supportingSignals: string[];
  opposingSignals: string[];
  predictionCorrect?: boolean;
  manualOverrides: number;
  stopMoves: number;
  ignoredSignal?: boolean;
  sourceOpportunityId?: string;
}

export interface TradeEvaluation {
  tradeId: string;
  predictionAccuracy: number;
  confidenceAccuracy: number;
  riskAccuracy: number;
  rewardAccuracy: number;
  timingAccuracy: number;
  trendAccuracy: number;
  executionQuality: number;
  overallScore: number;
  notes: string[];
}

export interface CalibrationBucket {
  bucket: string; // e.g. "90-100"
  predictedMid: number;
  sampleSize: number;
  actualWinRate: number;
  bias: "calibrated" | "overconfident" | "underconfident";
  gap: number;
}

export interface StrategyPerformance {
  strategy: StrategyKind;
  trades: number;
  wins: number;
  losses: number;
  winRate: number;
  avgRr: number;
  maxDrawdown: number;
  profitFactor: number;
  expectancy: number;
  avgHoldMinutes: number;
  sharpe?: number | null;
  sortino?: number | null;
}

export interface TraderProfile {
  userId: string;
  updatedAt: number;
  bestSession: string;
  weakestSession: string;
  bestPair: string;
  weakestPair: string;
  bestTimeframe: string;
  avgHoldMinutes: number;
  winRate: number;
  avgRiskPct: number;
  avgRr: number;
  totalTrades: number;
  coachScore: number;
  consistencyScore: number;
  preferredRiskMode: RiskMode;
  sessionStats: Record<string, { trades: number; winRate: number }>;
  pairStats: Record<string, { trades: number; winRate: number; avgRr: number }>;
  timeframeStats: Record<string, { trades: number; winRate: number }>;
}

export interface BehaviorReport {
  flags: Array<{
    flag: BehaviorFlag;
    count: number;
    severity: "low" | "medium" | "high";
    evidence: string;
  }>;
  generatedAt: number;
}

export interface MistakeEvent {
  id: string;
  at: number;
  flag: BehaviorFlag;
  description: string;
  impact: string;
  recommendation: string;
  tradeId?: string;
  evidenceCount: number;
}

export interface ExplainableRecommendation {
  id: string;
  createdAt: number;
  title: string;
  body: string;
  why: string;
  basedOn: string[];
  confidence: number;
  historicalSuccess?: number;
  expectedImprovement?: string;
  category: "session" | "pair" | "risk" | "behavior" | "strategy" | "rr" | "news";
}

export interface LearningGoal {
  id: string;
  title: string;
  metric:
    | "win_rate"
    | "avg_rr"
    | "max_daily_trades"
    | "max_risk_pct"
    | "reduce_overtrading"
    | "min_rr";
  target: number;
  current: number;
  unit: string;
  createdAt: number;
  achievedAt?: number;
}

export interface Achievement {
  id: string;
  code: string;
  title: string;
  description: string;
  unlockedAt?: number;
  progress: number;
  target: number;
}

export interface PredictionRecord {
  id: string;
  at: number;
  symbol: string;
  timeframe: string;
  bullishProbability: number;
  bearishProbability: number;
  confidence: number;
  actualOutcome?: OutcomeLabel;
  predictionCorrect?: boolean;
  evaluatedAt?: number;
}

export interface MarketMemoryEvent {
  id: string;
  at: number;
  userId: string;
  symbol: string;
  timeframe: string;
  session?: string;
  tags: string[]; // e.g. bullish_bos, order_block, liquidity_sweep
  confidence: number;
  outcome: OutcomeLabel;
  pnl?: number;
  contextHash: string;
  extras?: Record<string, string | number | boolean>;
}

export interface WeightVersion {
  version: string;
  weights: Record<string, number>;
  reason: string;
  evidence: string[];
  sampleSize: number;
  createdAt: number;
  active: boolean;
  rolledBack?: boolean;
}

export interface AnalyticsSnapshot {
  winRate: number;
  profitFactor: number;
  expectancy: number;
  avgRr: number;
  maxDrawdown: number;
  avgHoldMinutes: number;
  tradeCount: number;
  decisionAccuracy: number;
  confidenceAccuracy: number;
  coachScore: number;
  consistencyScore: number;
  sessionPerformance: Array<{ session: string; winRate: number; trades: number }>;
  pairPerformance: Array<{ symbol: string; winRate: number; trades: number; avgRr: number }>;
  weeklyTimeline: Array<{ week: string; winRate: number; avgRr: number; trades: number }>;
}

export interface BrainSimilarQuery {
  symbol?: string;
  timeframe?: string;
  tags: string[];
  session?: string;
  limit?: number;
}

export interface BrainSimilarHit {
  event: MarketMemoryEvent;
  similarity: number;
  reason: string;
}

export interface LearningStateBundle {
  userId: string;
  events: LearningEvent[];
  trades: TradeLearningRecord[];
  evaluations: TradeEvaluation[];
  predictions: PredictionRecord[];
  mistakes: MistakeEvent[];
  recommendations: ExplainableRecommendation[];
  goals: LearningGoal[];
  achievements: Achievement[];
  marketMemory: MarketMemoryEvent[];
  weightHistory: WeightVersion[];
  profile: TraderProfile | null;
  updatedAt: number;
}

export const DEFAULT_ACHIEVEMENTS: Omit<Achievement, "unlockedAt" | "progress">[] = [
  {
    id: "ach_100_trades",
    code: "100_trades",
    title: "100 Trades",
    description: "Complete 100 evaluated trades",
    target: 100,
  },
  {
    id: "ach_20_winning_days",
    code: "20_winning_days",
    title: "20 Winning Days",
    description: "Achieve 20 days with net positive PnL",
    target: 20,
  },
  {
    id: "ach_risk_discipline",
    code: "risk_discipline",
    title: "Risk Discipline",
    description: "30 trades without moving stop loss",
    target: 30,
  },
  {
    id: "ach_no_revenge",
    code: "no_revenge",
    title: "No Revenge Trading",
    description: "14 days without revenge-trading flags",
    target: 14,
  },
  {
    id: "ach_perfect_week",
    code: "perfect_week",
    title: "Perfect Week",
    description: "A week with ≥60% win rate and avg RR ≥ 1.5",
    target: 1,
  },
];
