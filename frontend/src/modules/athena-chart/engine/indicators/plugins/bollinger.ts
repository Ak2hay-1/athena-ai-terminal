import { computeBollinger } from "../calculations";
import type { IndicatorPlugin } from "../types";
import { drawLineSeries } from "./render-utils";

export const bollingerPlugin: IndicatorPlugin = {
  meta: {
    id: "bollinger",
    label: "Bollinger Bands",
    category: "overlay",
    defaultSettings: {
      length: 20,
      source: "close",
      color: "#64748b",
      thickness: 1,
      style: "solid",
      visible: true,
      mult: 2,
    },
  },
  calculate: ({ candles, settings }) => {
    const src = candles.map((c) => c[settings.source]);
    return computeBollinger(src, settings.length, Number(settings.mult ?? 2));
  },
  render: (ctx) => {
    const bb = ctx.values as {
      mid: Array<number | null>;
      upper: Array<number | null>;
      lower: Array<number | null>;
    };
    drawLineSeries(ctx, bb.upper);
    drawLineSeries(ctx, bb.mid);
    drawLineSeries(ctx, bb.lower);
  },
};
