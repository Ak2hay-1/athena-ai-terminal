import type { PaintContext } from "./context";

export function drawCandles(ctx: PaintContext, start: number, end: number): void {
  const { r, theme, layout, candles, viewport, chartType, priceY } = ctx;
  const rawBarW = (layout.plotWidth / viewport.span) * 0.7;
  const barW = Math.max(1, Math.round(rawBarW * 2) / 2);

  if (chartType === "line" || chartType === "area") {
    r.beginPath();
    let started = false;
    for (let i = start; i < end; i++) {
      const c = candles[i];
      const x = Math.round(
        viewport.indexToX(i + 0.5, layout.plotLeft, layout.plotWidth),
      );
      const y = Math.round(priceY(c.close, layout.mainTop, layout.mainH));
      if (!started) {
        r.moveTo(x, y);
        started = true;
      } else r.lineTo(x, y);
    }
    if (chartType === "area" && started) {
      const c2d = r.getCanvas2D();
      if (c2d) {
        const lastX = Math.round(
          viewport.indexToX(end - 0.5, layout.plotLeft, layout.plotWidth),
        );
        const firstX = Math.round(
          viewport.indexToX(start + 0.5, layout.plotLeft, layout.plotWidth),
        );
        r.lineTo(lastX, layout.mainTop + layout.mainH);
        r.lineTo(firstX, layout.mainTop + layout.mainH);
        r.closePath();
        const grad = c2d.createLinearGradient(
          0,
          layout.mainTop,
          0,
          layout.mainTop + layout.mainH,
        );
        grad.addColorStop(0, "rgba(255,107,0,0.35)");
        grad.addColorStop(1, "rgba(255,107,0,0.02)");
        c2d.fillStyle = grad;
        r.fill();
      }
    }
    r.setStrokeStyle(theme.crosshair);
    r.setLineWidth(2);
    r.stroke();
    return;
  }

  const hollow = chartType === "hollow";
  for (let i = start; i < end; i++) {
    const c = candles[i];
    const x = Math.round(
      viewport.indexToX(i + 0.5, layout.plotLeft, layout.plotWidth),
    );
    const yO = Math.round(priceY(c.open, layout.mainTop, layout.mainH));
    const yC = Math.round(priceY(c.close, layout.mainTop, layout.mainH));
    const yH = Math.round(priceY(c.high, layout.mainTop, layout.mainH));
    const yL = Math.round(priceY(c.low, layout.mainTop, layout.mainH));
    const up = c.close >= c.open;
    const gap = c.tick_volume === 0;
    const color = up ? theme.bullish : theme.bearish;
    r.setStrokeStyle(color);
    r.setFillStyle(hollow && up ? "transparent" : color);
    if (gap) {
      // Muted empty/gap candles
      r.setStrokeStyle(up ? "rgba(0,212,106,0.35)" : "rgba(255,77,77,0.35)");
      r.setFillStyle(up ? "rgba(0,212,106,0.2)" : "rgba(255,77,77,0.2)");
    }
    r.beginPath();
    r.moveTo(x + 0.5, yH);
    r.lineTo(x + 0.5, yL);
    r.stroke();
    const top = Math.min(yO, yC);
    const h = Math.max(1, Math.abs(yC - yO));
    const bodyX = Math.round(x - barW / 2) + 0.5;
    if (hollow && up) {
      r.strokeRect(bodyX, top, Math.max(1, barW), h);
    } else {
      r.fillRect(bodyX, top, Math.max(1, barW), h);
    }
  }
}
