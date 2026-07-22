import type { Candlestick } from "../../types";
import type { IChartRenderer } from "../renderers/types";
import type { Viewport } from "../viewport";
import type { PaneLayout } from "../../types";

export type IndicatorPlacement = "overlay" | "pane";

export interface IndicatorSettings {
  length: number;
  source: "close" | "open" | "high" | "low";
  color: string;
  thickness: number;
  style: "solid" | "dashed";
  visible: boolean;
  [key: string]: unknown;
}

export interface IndicatorMeta {
  id: string;
  label: string;
  category: IndicatorPlacement;
  defaultSettings: IndicatorSettings;
}

export interface IndicatorCalcContext {
  candles: Candlestick[];
  settings: IndicatorSettings;
}

export interface IndicatorRenderContext {
  r: IChartRenderer;
  viewport: Viewport;
  layout: PaneLayout;
  pane?: { top: number; height: number };
  priceY: (price: number, top: number, h: number) => number;
  values: unknown;
  settings: IndicatorSettings;
  start: number;
  end: number;
}

export interface IndicatorPlugin {
  meta: IndicatorMeta;
  calculate: (ctx: IndicatorCalcContext) => unknown;
  render: (ctx: IndicatorRenderContext) => void;
}

export interface IndicatorInstance {
  instanceId: string;
  pluginId: string;
  settings: IndicatorSettings;
  favorite?: boolean;
}
