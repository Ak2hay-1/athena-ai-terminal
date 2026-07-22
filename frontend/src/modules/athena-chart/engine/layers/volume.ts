import type { PaintContext } from "./context";

export function drawVolume(ctx: PaintContext, start: number, end: number): void {
  if (!ctx.indicators.volume) return;
  const { r, theme, layout, candles, viewport } = ctx;
  let maxVol = 1;
  for (let i = start; i < end; i++) {
    maxVol = Math.max(maxVol, candles[i]?.tick_volume || 0);
  }
  const volH = layout.mainH * 0.18;
  const base = layout.mainTop + layout.mainH;
  const barW = Math.max(1, (layout.plotWidth / viewport.span) * 0.7);
  for (let i = start; i < end; i++) {
    const c = candles[i];
    const x = viewport.indexToX(i + 0.5, layout.plotLeft, layout.plotWidth);
    const h = ((c.tick_volume || 0) / maxVol) * volH;
    r.setFillStyle(c.close >= c.open ? theme.volumeUp : theme.volumeDown);
    r.fillRect(x - barW / 2, base - h, barW, h);
  }
}
