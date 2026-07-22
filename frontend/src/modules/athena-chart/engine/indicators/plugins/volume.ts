import type { IndicatorPlugin } from "../types";

export const volumePlugin: IndicatorPlugin = {
  meta: {
    id: "volume",
    label: "Volume",
    category: "pane",
    defaultSettings: {
      length: 1,
      source: "close",
      color: "#00d46a",
      thickness: 1,
      style: "solid",
      visible: true,
    },
  },
  calculate: ({ candles }) => candles.map((c) => c.tick_volume),
  render: (ctx) => {
    if (!ctx.settings.visible || !ctx.pane) return;
    const values = ctx.values as number[];
    let max = 1;
    for (let i = ctx.start; i < ctx.end; i++) max = Math.max(max, values[i] || 0);
    const { r, viewport, layout, pane, settings } = ctx;
    const barW = Math.max(1, (layout.plotWidth / viewport.span) * 0.6);
    for (let i = ctx.start; i < ctx.end; i++) {
      const v = values[i] || 0;
      const h = (v / max) * pane.height * 0.9;
      const x = viewport.indexToX(i + 0.5, layout.plotLeft, layout.plotWidth);
      r.setFillStyle(settings.color);
      r.setGlobalAlpha(0.45);
      r.fillRect(x - barW / 2, pane.top + pane.height - h, barW, h);
      r.setGlobalAlpha(1);
    }
  },
};
