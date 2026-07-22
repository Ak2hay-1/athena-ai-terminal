import type { Candlestick } from "./market";

export type ChartType = "candles" | "hollow" | "line" | "area";

export type DrawingTool =
  | "crosshair"
  | "cursor"
  | "trend"
  | "hline"
  | "vline"
  | "ray"
  | "rect"
  | "circle"
  | "text"
  | "arrow"
  | "fib"
  | "measure"
  | "erase"
  | "magnet"
  | "zoom"
  | "hand";

export type MagnetMode = "strong" | "weak" | "off";

export type DrawingType =
  | "trend"
  | "hline"
  | "vline"
  | "ray"
  | "rect"
  | "circle"
  | "arrow"
  | "text"
  | "fib"
  | "measure";

export type DrawingLayerId = "indicators" | "drawings" | "ai" | "trades" | "crosshair";

export type ZoneKind = "support" | "resistance" | "supply" | "demand" | "custom";
export type ArrowStyle = "bullish" | "bearish" | "neutral";
export type RayDirection = "left" | "right" | "both";

export interface DrawingPoint {
  /** Bar time in unix seconds */
  t: number;
  /** Price */
  p: number;
}

export interface DrawingStyle {
  color: string;
  lineWidth: number;
  dash: number[];
  fillOpacity: number;
  fontSize: number;
  fontBold: boolean;
  fontItalic: boolean;
  background: string | null;
}

export const DEFAULT_DRAWING_STYLE: DrawingStyle = {
  color: "#ff6b00",
  lineWidth: 1.5,
  dash: [],
  fillOpacity: 0.08,
  fontSize: 12,
  fontBold: false,
  fontItalic: false,
  background: null,
};

export interface DrawingMeta {
  zoneKind?: ZoneKind;
  arrowStyle?: ArrowStyle;
  rayDirection?: RayDirection;
  text?: string;
  rotation?: number;
  measureSticky?: boolean;
}

export interface DrawingObject {
  id: string;
  type: DrawingType;
  points: DrawingPoint[];
  style: DrawingStyle;
  layer: DrawingLayerId;
  zIndex: number;
  locked: boolean;
  visible: boolean;
  selected: boolean;
  meta: DrawingMeta;
  createdAt: number;
  updatedAt: number;
}

/** Legacy shape used by Markets AthenaChart — kept for compatibility. */
export type ChartDrawing =
  | {
      id: string;
      type: "trend" | "ray";
      t1: number;
      p1: number;
      t2: number;
      p2: number;
    }
  | {
      id: string;
      type: "hline";
      price: number;
    }
  | {
      id: string;
      type: "rect";
      t1: number;
      p1: number;
      t2: number;
      p2: number;
    }
  | {
      id: string;
      type: "fib";
      t1: number;
      p1: number;
      t2: number;
      p2: number;
    };

export interface IndicatorFlags {
  ema20: boolean;
  ema50: boolean;
  sma20: boolean;
  sma50: boolean;
  sma200: boolean;
  bollinger: boolean;
  vwap: boolean;
  atr: boolean;
  rsi: boolean;
  macd: boolean;
  volume: boolean;
  priceLine: boolean;
}

export const DEFAULT_INDICATORS: IndicatorFlags = {
  ema20: false,
  ema50: false,
  sma20: false,
  sma50: false,
  sma200: false,
  bollinger: false,
  vwap: false,
  atr: false,
  rsi: false,
  macd: false,
  volume: true,
  priceLine: true,
};

export interface ChartLevels {
  entry?: number;
  stopLoss?: number;
  takeProfit?: number;
}

export interface ChartMarker {
  time: string;
  position?: "aboveBar" | "belowBar";
  shape?: "arrowUp" | "arrowDown" | "circle" | "square";
  color?: string;
  text?: string;
}

export interface ViewportState {
  from: number;
  to: number;
}

export interface CrosshairState {
  x: number;
  y: number;
  barIndex: number;
  price: number;
  visible: boolean;
}

export interface SmartCursorInfo {
  price: number;
  timeSec: number;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  pctChange: number | null;
  spread: number | null;
  atr: number | null;
}

export interface PaneLayout {
  plotLeft: number;
  plotWidth: number;
  mainTop: number;
  mainH: number;
  rsiTop: number;
  rsiH: number;
  macdTop: number;
  macdH: number;
  showRsi: boolean;
  showMacd: boolean;
  plotBottom: number;
  panes: Array<{ id: string; top: number; height: number }>;
}

export interface ContextMenuRequest {
  x: number;
  y: number;
  drawingId: string | null;
}

export interface EngineOptions {
  mode?: "advanced" | "overview";
  chartType?: ChartType;
  indicators?: IndicatorFlags;
  levels?: ChartLevels | null;
  markers?: ChartMarker[];
  drawings?: ChartDrawing[];
  drawingObjects?: DrawingObject[];
  tool?: DrawingTool;
  magnet?: boolean;
  magnetMode?: MagnetMode;
  showSessions?: boolean;
  sessionFlags?: Record<string, boolean>;
  hideChrome?: boolean;
  onNeedMoreHistory?: () => void;
  historyThreshold?: number;
  isLoadingHistory?: boolean;
  onDrawingComplete?: (drawing: ChartDrawing) => void;
  onDrawingsChange?: (objects: DrawingObject[]) => void;
  onSelectionChange?: (ids: string[]) => void;
  onContextMenu?: (req: ContextMenuRequest) => void;
  onTextEdit?: (id: string, text: string, screen: { x: number; y: number }) => void;
  onCrosshair?: (
    candle: Candlestick | null,
    extras: Array<{ label: string; value: string; color?: string }>,
    smart?: SmartCursorInfo | null,
  ) => void;
  onFps?: (fps: number) => void;
  onViewportChange?: (state: ViewportState) => void;
  onHistoryChange?: (canUndo: boolean, canRedo: boolean) => void;
  /** Intelligence layer snapshot (rule-engine overlays). */
  intelligenceSnapshot?: import("../intelligence/types").AnalysisSnapshot | null;
  intelligenceOverlays?: import("../intelligence/types").OverlayVisibility;
  /** Decision engine snapshot (trade levels / badges). */
  decisionSnapshot?: import("../decision-engine/types").DecisionSnapshot | null;
  decisionOverlays?: import("../decision-engine/types").DecisionOverlayVisibility;
}
