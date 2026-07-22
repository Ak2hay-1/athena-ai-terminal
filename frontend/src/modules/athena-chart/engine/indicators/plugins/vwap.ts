import { computeVwap } from "../calculations";
import type { IndicatorPlugin } from "../types";
import { drawLineSeries } from "./render-utils";

export const vwapPlugin: IndicatorPlugin = {
  meta: {
    id: "vwap",
    label: "VWAP",
    category: "overlay",
    defaultSettings: {
      length: 1,
      source: "close",
      color: "#14b8a6",
      thickness: 1,
      style: "solid",
      visible: true,
    },
  },
  calculate: ({ candles }) => computeVwap(candles),
  render: (ctx) => drawLineSeries(ctx, ctx.values as Array<number | null>),
};
