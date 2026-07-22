/**
 * Athena Chart — public module API.
 */

export { ChartController, ChartEngine, createChart } from "./engine";
export {
  TimeBucketEngine,
  bucketStartUtcMs,
  fillMissingBuckets,
  validateSeries,
} from "./engine/time";
export { Viewport } from "./engine/viewport";
export type { IChartRenderer } from "./engine/renderers/types";
export { createCanvasRenderer } from "./engine/renderers/canvas";
export { createWebGlRenderer, isWebGlSupported } from "./engine/renderers/webgl";
export {
  DrawingEngine,
  DrawingManager,
  createDrawingObject,
  legacyToObject,
} from "./engine/drawing";
export {
  IndicatorManager,
  listIndicatorPlugins,
  getIndicatorPlugin,
} from "./engine/indicators";
export { ATHENA_CHART_THEME } from "./theme";
export type { AthenaChartTheme } from "./theme";

export type {
  Candlestick,
  Tick,
  Trade,
  VolumeBar,
  IndicatorDefinition,
  MarketSession,
  ChartType,
  DrawingTool,
  MagnetMode,
  DrawingObject,
  DrawingType,
  IndicatorFlags,
  ChartLevels,
  ChartMarker,
  ChartDrawing,
  EngineOptions,
  ViewportState,
  CrosshairState,
  SmartCursorInfo,
} from "./types";
export { DEFAULT_INDICATORS, DEFAULT_DRAWING_STYLE } from "./types";

export {
  useChartStore,
  useViewportStore,
  useDrawingStore,
  useIndicatorStore,
  useReplayStore,
  useChartUiStore,
  useSessionStore,
  useWatchlistStore,
  useAlertStore,
} from "./store";

export {
  chartService,
  marketDataService,
  indicatorService,
  workspaceService,
} from "./services";
export { useLiveCandles, useMockCandles, useChartEngine } from "./hooks";
export {
  CHART_TIMEFRAMES,
  LIVE_CHART_TIMEFRAMES,
  toApiTimeframe,
  fromApiTimeframe,
} from "./utils/timeframes";
export { generateStressDrawings, generateStressCandles } from "./utils/stress";

export { AthenaChartPage } from "./pages/AthenaChartPage";
export { ChartTerminalLayout } from "./components/ChartTerminalLayout";
export { ChartCanvas } from "./components/ChartCanvas";
export { ChartContainer } from "./components/ChartContainer";

export {
  runAnalysisPipeline,
  getIntelligenceService,
  useIntelligenceStore,
  renderIntelligenceOverlays,
  DEFAULT_INTEL_SETTINGS,
} from "./intelligence";
export type { AnalysisSnapshot, IntelligenceSettings } from "./intelligence";

export {
  runDecisionPipeline,
  getDecisionService,
  useDecisionStore,
  renderDecisionOverlays,
  DEFAULT_DECISION_SETTINGS,
} from "./decision-engine";
export type { DecisionSnapshot, DecisionSettings, TradeOpportunity } from "./decision-engine";

export {
  CopilotPanel,
  useCopilotStore,
  getCopilotService,
  buildAthenaContext,
  getAIProvider,
} from "./copilot";
export type { AthenaStructuredContext, CopilotSettings } from "./copilot";
