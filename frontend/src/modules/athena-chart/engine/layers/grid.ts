import { niceTicks } from "../../utils/format";
import type { PaintContext } from "./context";

export function drawGrid(ctx: PaintContext): void {
  const { r, theme, layout, priceMin, priceMax, priceY } = ctx;
  r.setStrokeStyle(theme.grid);
  r.setLineWidth(1);
  const ticks = niceTicks(priceMin, priceMax, 6);
  for (const p of ticks) {
    const y = priceY(p, layout.mainTop, layout.mainH);
    r.beginPath();
    r.moveTo(0, y);
    r.lineTo(layout.plotWidth, y);
    r.stroke();
  }
}
