import { computeAtr } from "../calculations";
import type { IndicatorPlugin } from "../types";
import { drawLineSeries } from "./render-utils";

export const atrPlugin: IndicatorPlugin = {
  meta: {
    id: "atr",
    label: "ATR",
    category: "overlay",
    defaultSettings: {
      length: 14,
      source: "close",
      color: "#ec4899",
      thickness: 1,
      style: "solid",
      visible: true,
    },
  },
  calculate: ({ candles, settings }) => computeAtr(candles, settings.length),
  render: (ctx) => drawLineSeries(ctx, ctx.values as Array<number | null>),
};
