import type { IndicatorRenderContext } from "../types";

export function drawLineSeries(
  ctx: IndicatorRenderContext,
  values: Array<number | null>,
  yOf?: (v: number) => number,
): void {
  if (!ctx.settings.visible) return;
  const { r, viewport, layout, start, end, settings } = ctx;
  const mapY =
    yOf ??
    ((v: number) => ctx.priceY(v, layout.mainTop, layout.mainH));
  r.setStrokeStyle(settings.color);
  r.setLineWidth(settings.thickness);
  r.setLineDash(settings.style === "dashed" ? [4, 3] : []);
  r.beginPath();
  let started = false;
  for (let i = start; i < end; i++) {
    const v = values[i];
    if (v == null || !Number.isFinite(v)) {
      started = false;
      continue;
    }
    const x = viewport.indexToX(i + 0.5, layout.plotLeft, layout.plotWidth);
    const y = mapY(v);
    if (!started) {
      r.moveTo(x, y);
      started = true;
    } else r.lineTo(x, y);
  }
  r.stroke();
  r.setLineDash([]);
}
