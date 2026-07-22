import { computeMacd } from "../calculations";
import type { IndicatorPlugin } from "../types";

export const macdPlugin: IndicatorPlugin = {
  meta: {
    id: "macd",
    label: "MACD",
    category: "pane",
    defaultSettings: {
      length: 12,
      source: "close",
      color: "#3b82f6",
      thickness: 1,
      style: "solid",
      visible: true,
      slow: 26,
      signal: 9,
    },
  },
  calculate: ({ candles, settings }) => {
    const src = candles.map((c) => c[settings.source]);
    return computeMacd(
      src,
      settings.length,
      Number(settings.slow ?? 26),
      Number(settings.signal ?? 9),
    );
  },
  render: (ctx) => {
    if (!ctx.pane || !ctx.settings.visible) return;
    const macd = ctx.values as {
      macd: Array<number | null>;
      signal: Array<number | null>;
      hist: Array<number | null>;
    };
    const pane = ctx.pane;
    let min = 0;
    let max = 0;
    for (let i = ctx.start; i < ctx.end; i++) {
      for (const arr of [macd.hist, macd.macd, macd.signal]) {
        const v = arr[i];
        if (v != null) {
          min = Math.min(min, v);
          max = Math.max(max, v);
        }
      }
    }
    const span = Math.max(1e-9, max - min);
    const yOf = (v: number) => pane.top + ((max - v) / span) * pane.height;
    const { r, viewport, layout } = ctx;
    const barW = Math.max(1, (layout.plotWidth / viewport.span) * 0.5);
    const zeroY = yOf(0);
    for (let i = ctx.start; i < ctx.end; i++) {
      const h = macd.hist[i];
      if (h == null) continue;
      const x = viewport.indexToX(i + 0.5, layout.plotLeft, layout.plotWidth);
      const y = yOf(h);
      r.setFillStyle(h >= 0 ? "rgba(0,212,106,0.4)" : "rgba(255,77,77,0.4)");
      r.fillRect(x - barW / 2, Math.min(y, zeroY), barW, Math.max(1, Math.abs(y - zeroY)));
    }
    const stroke = (vals: Array<number | null>, color: string) => {
      r.setStrokeStyle(color);
      r.beginPath();
      let started = false;
      for (let i = ctx.start; i < ctx.end; i++) {
        const v = vals[i];
        if (v == null) {
          started = false;
          continue;
        }
        const x = viewport.indexToX(i + 0.5, layout.plotLeft, layout.plotWidth);
        const y = yOf(v);
        if (!started) {
          r.moveTo(x, y);
          started = true;
        } else r.lineTo(x, y);
      }
      r.stroke();
    };
    stroke(macd.macd, ctx.settings.color);
    stroke(macd.signal, "#ef4444");
  },
};
