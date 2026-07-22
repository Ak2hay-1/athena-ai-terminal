import type {
  DecisionOverlayVisibility,
  DecisionSnapshot,
  TradeOpportunity,
} from "../types";
import type { AthenaChartTheme } from "../../theme";
import type { IChartRenderer } from "../../engine/renderers/types";
import type { Viewport } from "../../engine/viewport";
import type { PaneLayout } from "../../types";
import { formatPriceLabel } from "../../utils/format";

export interface DecisionOverlayContext {
  r: IChartRenderer;
  theme: AthenaChartTheme;
  viewport: Viewport;
  layout: PaneLayout;
  priceY: (price: number, top: number, h: number) => number;
  overlays: DecisionOverlayVisibility;
  snapshot: DecisionSnapshot | null;
}

/** Render decision overlays — independent of chart engine internals. */
export function renderDecisionOverlays(ctx: DecisionOverlayContext): void {
  const { r, theme, viewport, layout, priceY, overlays: o, snapshot } = ctx;
  const opp = snapshot?.opportunity;
  if (!opp) return;

  const { mainTop, mainH, plotLeft, plotWidth } = layout;
  const x0 = plotLeft + plotWidth * 0.55;
  const x1 = plotLeft + plotWidth;

  if (o.buyZone && opp.buyZone) {
    const y1 = priceY(opp.buyZone.top, mainTop, mainH);
    const y2 = priceY(opp.buyZone.bottom, mainTop, mainH);
    r.setFillStyle("rgba(34, 197, 94, 0.12)");
    r.fillRect(x0, Math.min(y1, y2), x1 - x0, Math.abs(y2 - y1));
    r.setStrokeStyle("rgba(34, 197, 94, 0.45)");
    r.setLineWidth(1);
    r.strokeRect(x0, Math.min(y1, y2), x1 - x0, Math.abs(y2 - y1));
  }

  if (o.sellZone && opp.sellZone) {
    const y1 = priceY(opp.sellZone.top, mainTop, mainH);
    const y2 = priceY(opp.sellZone.bottom, mainTop, mainH);
    r.setFillStyle("rgba(239, 68, 68, 0.12)");
    r.fillRect(x0, Math.min(y1, y2), x1 - x0, Math.abs(y2 - y1));
    r.setStrokeStyle("rgba(239, 68, 68, 0.45)");
    r.setLineWidth(1);
    r.strokeRect(x0, Math.min(y1, y2), x1 - x0, Math.abs(y2 - y1));
  }

  if (opp.direction === "flat") {
    drawBadges(r, theme, layout, opp, o);
    return;
  }

  const e = opp.activeEntry;
  const drawLevel = (price: number, color: string, label: string, dashed = false) => {
    const y = priceY(price, mainTop, mainH);
    r.setStrokeStyle(color);
    r.setLineWidth(1);
    if (dashed) r.setLineDash([4, 3]);
    r.beginPath();
    r.moveTo(plotLeft, y);
    r.lineTo(plotLeft + plotWidth, y);
    r.stroke();
    if (dashed) r.setLineDash([]);
    r.setFillStyle(color);
    r.setFont(theme.fontSmall);
    r.fillText(`${label} ${formatPriceLabel(price)}`, plotLeft + 4, y - 3);
  };

  if (o.entry) drawLevel(e.entry, theme.crosshair ?? "#38bdf8", "Entry");
  if (o.stopLoss) drawLevel(e.stopLoss, theme.bearish, "SL");
  if (o.takeProfits) {
    drawLevel(e.takeProfit1, theme.bullish, "TP1", true);
    drawLevel(e.takeProfit2, theme.bullish, "TP2", true);
    drawLevel(e.takeProfit3, theme.bullish, "TP3", true);
  }

  // Unused viewport keep for API parity / future bar anchoring
  void viewport;

  drawBadges(r, theme, layout, opp, o);
}

function drawBadges(
  r: IChartRenderer,
  theme: AthenaChartTheme,
  layout: PaneLayout,
  opp: TradeOpportunity,
  o: DecisionOverlayVisibility,
) {
  const parts: string[] = [];
  if (o.gradeBadge) parts.push(`Grade ${opp.grade}`);
  if (o.confidenceBadge) {
    parts.push(
      `${Math.round(opp.confidence.score)}% ${opp.confidence.label.replace(/_/g, " ")}`,
    );
  }
  if (o.probabilityBadge) {
    parts.push(
      `B${Math.round(opp.probability.bullish)}/S${Math.round(opp.probability.bearish)}`,
    );
  }
  if (o.riskBadge) parts.push(`Risk ${opp.risk.category}`);
  if (!parts.length) return;

  const text = parts.join(" · ");
  const x = layout.plotLeft + 8;
  const y = layout.mainTop + 16;
  r.setFillStyle("rgba(10,10,10,0.72)");
  r.fillRect(x - 4, y - 12, Math.min(layout.plotWidth - 16, text.length * 6.2), 18);
  r.setFillStyle(theme.text);
  r.setFont(theme.fontSmall);
  r.fillText(text, x, y);
}
