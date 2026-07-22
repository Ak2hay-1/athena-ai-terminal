import type { Candlestick } from "../../types";

/** Shared scoring metadata — every detected object is explainable & traceable. */
export interface DetectionScore {
  confidence: number; // 0-100
  strength: number; // 0-100
  ageBars: number;
  retests: number;
  validity: number; // 0-100
  status: "active" | "mitigated" | "invalid" | "filled" | "partial";
  score: number; // composite 0-100
}

export interface TraceRef {
  /** Candle indices that produced this detection */
  candleIndices: number[];
  /** Human-readable rule id e.g. "swing.fractal.v1" */
  ruleId: string;
  notes?: string;
}

export interface ScoredObject extends DetectionScore {
  id: string;
  trace: TraceRef;
  createdAt: number;
}

export type SwingKind = "high" | "low";
export type StructureLabel = "HH" | "HL" | "LH" | "LL" | "BOS" | "CHOCH";
export type TrendClass =
  | "strong_bullish"
  | "bullish"
  | "weak_bullish"
  | "range"
  | "weak_bearish"
  | "bearish"
  | "strong_bearish";

export interface SwingPoint extends ScoredObject {
  kind: SwingKind;
  index: number;
  time: string;
  price: number;
  fractal: boolean;
}

export interface StructureEvent extends ScoredObject {
  label: StructureLabel;
  index: number;
  time: string;
  price: number;
  direction: "bullish" | "bearish";
  scope: "internal" | "external";
}

export interface TrendState {
  classification: TrendClass;
  confidence: number;
  direction: "bullish" | "bearish" | "neutral";
  swingBias: number;
}

export interface PriceLevel extends ScoredObject {
  kind: "support" | "resistance";
  price: number;
  tests: number;
  fresh: boolean;
  broken: boolean;
  reactionStrength: number;
}

export interface Zone extends ScoredObject {
  kind: "demand" | "supply";
  top: number;
  bottom: number;
  startIndex: number;
  endIndex: number;
  mitigated: boolean;
  invalid: boolean;
  freshness: number;
}

export interface OrderBlock extends ScoredObject {
  bias: "bullish" | "bearish";
  top: number;
  bottom: number;
  startIndex: number;
  endIndex: number;
  breaker: boolean;
  mitigated: boolean;
  invalid: boolean;
}

export interface FairValueGap extends ScoredObject {
  bias: "bullish" | "bearish";
  top: number;
  bottom: number;
  startIndex: number;
  endIndex: number;
  fillRatio: number; // 0-1
}

export interface LiquidityPool extends ScoredObject {
  kind:
    | "equal_highs"
    | "equal_lows"
    | "pool"
    | "sweep"
    | "stop_hunt"
    | "resting"
    | "internal"
    | "external";
  price: number;
  index: number;
  time: string;
  importance: number;
}

export interface Imbalance extends ScoredObject {
  kind: "price" | "volume" | "momentum";
  index: number;
  gapSize: number;
  direction: "bullish" | "bearish";
}

export interface PremiumDiscount {
  equilibrium: number;
  premiumHigh: number;
  premiumLow: number;
  discountHigh: number;
  discountLow: number;
  swingHigh: number;
  swingLow: number;
}

export interface SessionInfo {
  id: string;
  name: string;
  active: boolean;
  open: number;
  high: number;
  low: number;
  close: number;
  killZone: boolean;
}

export interface VolumeIntel {
  participation: "high" | "low" | "normal";
  pressure: "buying" | "selling" | "balanced";
  absorption: boolean;
  exhaustion: boolean;
  climax: boolean;
  divergence: boolean;
  score: number;
}

export type PatternKind =
  | "double_top"
  | "double_bottom"
  | "triangle"
  | "flag"
  | "pennant"
  | "rectangle"
  | "channel"
  | "wedge"
  | "cup_handle"
  | "head_shoulders"
  | "inv_head_shoulders"
  | "expanding_triangle"
  | "descending_triangle"
  | "ascending_triangle";

export interface PatternHit extends ScoredObject {
  kind: PatternKind;
  startIndex: number;
  endIndex: number;
  direction: "bullish" | "bearish" | "neutral";
}

export interface ConfluenceResult {
  bullishScore: number;
  bearishScore: number;
  neutralScore: number;
  overallConfidence: number;
  drivers: Array<{ source: string; weight: number; bias: "bullish" | "bearish" | "neutral" }>;
}

export interface IntelligenceEvent {
  id: string;
  time: string;
  timeSec: number;
  label: string;
  kind: string;
  confidence: number;
  bias?: "bullish" | "bearish" | "neutral";
}

export interface MtfBias {
  timeframe: string;
  classification: TrendClass;
  confidence: number;
}

export interface MtfAlignment {
  frames: MtfBias[];
  agreementPct: number;
  dominant: TrendClass;
}

export interface OverlayVisibility {
  structure: boolean;
  swings: boolean;
  orderBlocks: boolean;
  fvg: boolean;
  supplyDemand: boolean;
  liquidity: boolean;
  supportResistance: boolean;
  trend: boolean;
  premiumDiscount: boolean;
  sessions: boolean;
  patterns: boolean;
}

export interface IntelligenceSettings {
  swingLength: number;
  sensitivity: number; // 0-1
  noiseFilter: boolean;
  adaptiveMode: boolean;
  detectionMode: "strict" | "balanced" | "aggressive";
  confidenceThreshold: number;
  performanceMode: "full" | "fast";
  overlays: OverlayVisibility;
}

export const DEFAULT_OVERLAYS: OverlayVisibility = {
  structure: true,
  swings: true,
  orderBlocks: true,
  fvg: true,
  supplyDemand: true,
  liquidity: true,
  supportResistance: true,
  trend: true,
  premiumDiscount: false,
  sessions: false,
  patterns: true,
};

export const DEFAULT_INTEL_SETTINGS: IntelligenceSettings = {
  swingLength: 5,
  sensitivity: 0.55,
  noiseFilter: true,
  adaptiveMode: true,
  detectionMode: "balanced",
  confidenceThreshold: 40,
  performanceMode: "full",
  overlays: { ...DEFAULT_OVERLAYS },
};

export interface AnalysisSnapshot {
  symbol: string;
  timeframe: string;
  candleCount: number;
  lastTime: string;
  swings: SwingPoint[];
  structure: StructureEvent[];
  trend: TrendState;
  levels: PriceLevel[];
  zones: Zone[];
  orderBlocks: OrderBlock[];
  fvgs: FairValueGap[];
  liquidity: LiquidityPool[];
  imbalances: Imbalance[];
  premiumDiscount: PremiumDiscount | null;
  sessions: SessionInfo[];
  volume: VolumeIntel;
  patterns: PatternHit[];
  confluence: ConfluenceResult;
  events: IntelligenceEvent[];
  mtf: MtfAlignment | null;
  analyzedAt: number;
}

export interface AnalysisInput {
  candles: Candlestick[];
  symbol: string;
  timeframe: string;
  settings: IntelligenceSettings;
  /** Optional extra TF series for MTF */
  multiTimeframe?: Array<{ timeframe: string; candles: Candlestick[] }>;
}
