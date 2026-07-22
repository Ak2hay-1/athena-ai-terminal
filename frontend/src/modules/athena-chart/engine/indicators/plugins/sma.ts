import { computeSma } from "../calculations";
import type { IndicatorPlugin } from "../types";
import { drawLineSeries } from "./render-utils";

export const smaPlugin: IndicatorPlugin = {
  meta: {
    id: "sma",
    label: "SMA",
    category: "overlay",
    defaultSettings: {
      length: 20,
      source: "close",
      color: "#22d3ee",
      thickness: 1,
      style: "solid",
      visible: true,
    },
  },
  calculate: ({ candles, settings }) => {
    const src = candles.map((c) => c[settings.source]);
    return computeSma(src, settings.length);
  },
  render: (ctx) => drawLineSeries(ctx, ctx.values as Array<number | null>),
};
