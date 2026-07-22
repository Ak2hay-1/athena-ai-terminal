import type { AthenaChartTheme } from "../../theme";
import type {
  Candlestick,
  ChartDrawing,
  ChartLevels,
  ChartMarker,
  ChartType,
  CrosshairState,
  IndicatorFlags,
  PaneLayout,
} from "../../types";
import type { IChartRenderer } from "../renderers/types";
import type { Viewport } from "../viewport";

export const RIGHT_AXIS = 72;
export const BOTTOM_AXIS = 36;
export const PAD_TOP = 8;

export interface PaintContext {
  r: IChartRenderer;
  theme: AthenaChartTheme;
  viewport: Viewport;
  width: number;
  height: number;
  candles: Candlestick[];
  chartType: ChartType;
  indicators: IndicatorFlags;
  levels: ChartLevels | null;
  markers: ChartMarker[];
  drawings: ChartDrawing[];
  draft: {
    type: string;
    i1: number;
    p1: number;
    i2: number;
    p2: number;
  } | null;
  crosshair: CrosshairState;
  priceMin: number;
  priceMax: number;
  mode: "advanced" | "overview";
  layout: PaneLayout;
  priceY: (price: number, top: number, h: number) => number;
  /** Instrument symbol for price precision (e.g. EURUSD). */
  symbol?: string;
}
