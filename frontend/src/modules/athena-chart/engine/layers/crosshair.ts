import { formatCrosshairTime, formatPriceLabel } from "../../utils/format";
import { PAD_TOP, RIGHT_AXIS, type PaintContext } from "./context";

export function drawCrosshair(ctx: PaintContext): void {
  if (!ctx.crosshair.visible || ctx.mode !== "advanced") return;
  const { r, theme, layout, crosshair: ch, symbol } = ctx;

  r.setStrokeStyle(theme.crosshair);
  r.setLineDash([4, 3]);
  r.beginPath();
  r.moveTo(ch.x, PAD_TOP);
  r.lineTo(ch.x, layout.plotBottom);
  r.moveTo(0, ch.y);
  r.lineTo(layout.plotWidth, ch.y);
  r.stroke();
  r.setLineDash([]);

  // Right-axis price label at cursor
  const priceText = formatPriceLabel(ch.price, symbol);
  const priceBoxH = 16;
  r.setFillStyle(theme.crosshair);
  r.fillRect(layout.plotWidth, ch.y - priceBoxH / 2, RIGHT_AXIS, priceBoxH);
  r.setFillStyle("#000");
  r.setFont(theme.fontSmall);
  r.fillText(priceText, layout.plotWidth + 4, ch.y + 3);

  // Bottom time label under cursor (TradingView-style)
  if (ch.barIndex >= 0 && ctx.candles[ch.barIndex]) {
    const sec = Math.floor(
      new Date(ctx.candles[ch.barIndex].time).getTime() / 1000,
    );
    const { date, time } = formatCrosshairTime(sec);
    const boxW = 92;
    const boxH = 32;
    const bx = Math.max(
      4,
      Math.min(ch.x - boxW / 2, layout.plotWidth - boxW - 4),
    );
    const by = layout.plotBottom - boxH - 2;
    r.setFillStyle("rgba(0,0,0,0.82)");
    r.fillRect(bx, by, boxW, boxH);
    r.setStrokeStyle(theme.crosshair);
    r.strokeRect(bx, by, boxW, boxH);
    r.setFillStyle("#fff");
    r.setFont(theme.fontSmall);
    r.fillText(date, bx + 8, by + 12);
    r.fillText(time, bx + 8, by + 25);
  }
}
