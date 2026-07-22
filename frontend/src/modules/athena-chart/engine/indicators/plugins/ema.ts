import { computeEma } from "../calculations";
import type { IndicatorPlugin } from "../types";
import { drawLineSeries } from "./render-utils";

export const emaPlugin: IndicatorPlugin = {
  meta: {
    id: "ema",
    label: "EMA",
    category: "overlay",
    defaultSettings: {
      length: 20,
      source: "close",
      color: "#3b82f6",
      thickness: 1,
      style: "solid",
      visible: true,
    },
  },
  calculate: ({ candles, settings }) => {
    const src = candles.map((c) => c[settings.source]);
    return computeEma(src, settings.length);
  },
  render: (ctx) => {
    drawLineSeries(ctx, ctx.values as Array<number | null>);
  },
};
