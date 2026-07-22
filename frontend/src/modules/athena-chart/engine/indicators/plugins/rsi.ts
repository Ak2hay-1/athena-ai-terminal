import { computeRsi } from "../calculations";
import type { IndicatorPlugin } from "../types";
import { drawLineSeries } from "./render-utils";

export const rsiPlugin: IndicatorPlugin = {
  meta: {
    id: "rsi",
    label: "RSI",
    category: "pane",
    defaultSettings: {
      length: 14,
      source: "close",
      color: "#f59e0b",
      thickness: 1,
      style: "solid",
      visible: true,
    },
  },
  calculate: ({ candles, settings }) => {
    const src = candles.map((c) => c[settings.source]);
    return computeRsi(src, settings.length);
  },
  render: (ctx) => {
    if (!ctx.pane) return;
    const pane = ctx.pane;
    drawLineSeries(ctx, ctx.values as Array<number | null>, (v) =>
      pane.top + ((100 - v) / 100) * pane.height,
    );
  },
};
