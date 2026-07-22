import type { AnalysisSnapshot, OverlayVisibility } from "../types";
import type { AthenaChartTheme } from "../../theme";
import type { IChartRenderer } from "../../engine/renderers/types";
import type { Viewport } from "../../engine/viewport";
import type { PaneLayout } from "../../types";
import { formatPriceLabel } from "../../utils/format";
import { candleTimeSec } from "../../utils/format";

export interface OverlayRenderContext {
  r: IChartRenderer;
  theme: AthenaChartTheme;
  viewport: Viewport;
  layout: PaneLayout;
  priceY: (price: number, top: number, h: number) => number;
  indexFromTime: (t: string) => number;
  overlays: OverlayVisibility;
  snapshot: AnalysisSnapshot;
}

/** AI overlay layer — independent of drawings / indicators. */
export function renderIntelligenceOverlays(ctx: OverlayRenderContext): void {
  const { snapshot: s, overlays: o, r, layout, viewport, priceY, theme } = ctx;
  if (!s) return;

  if (o.orderBlocks) {
    for (const ob of s.orderBlocks.filter((x) => x.status === "active").slice(-8)) {
      const x1 = viewport.indexToX(ob.startIndex, layout.plotLeft, layout.plotWidth);
      const x2 = layout.plotWidth;
      const y1 = priceY(ob.top, layout.mainTop, layout.mainH);
      const y2 = priceY(ob.bottom, layout.mainTop, layout.mainH);
      const color =
        ob.bias === "bullish" ? "rgba(0,212,106,0.12)" : "rgba(255,77,77,0.12)";
      r.setFillStyle(color);
      r.fillRect(x1, Math.min(y1, y2), Math.max(4, x2 - x1), Math.abs(y2 - y1));
      r.setStrokeStyle(ob.bias === "bullish" ? theme.bullish : theme.bearish);
      r.setLineWidth(1);
      r.strokeRect(x1, Math.min(y1, y2), Math.max(4, x2 - x1), Math.abs(y2 - y1));
    }
  }

  if (o.fvg) {
    for (const f of s.fvgs.filter((x) => x.status === "active" || x.status === "partial").slice(-10)) {
      const x1 = viewport.indexToX(f.startIndex, layout.plotLeft, layout.plotWidth);
      const x2 = viewport.indexToX(f.endIndex + 1, layout.plotLeft, layout.plotWidth);
      const y1 = priceY(f.top, layout.mainTop, layout.mainH);
      const y2 = priceY(f.bottom, layout.mainTop, layout.mainH);
      r.setFillStyle(
        f.bias === "bullish" ? "rgba(56,189,248,0.1)" : "rgba(251,146,60,0.1)",
      );
      r.fillRect(x1, Math.min(y1, y2), Math.max(2, x2 - x1), Math.abs(y2 - y1));
    }
  }

  if (o.supplyDemand) {
    for (const z of s.zones.filter((x) => x.status === "active").slice(-8)) {
      const x1 = viewport.indexToX(z.startIndex, layout.plotLeft, layout.plotWidth);
      const y1 = priceY(z.top, layout.mainTop, layout.mainH);
      const y2 = priceY(z.bottom, layout.mainTop, layout.mainH);
      r.setFillStyle(
        z.kind === "demand" ? "rgba(0,212,106,0.08)" : "rgba(255,77,77,0.08)",
      );
      r.fillRect(x1, Math.min(y1, y2), layout.plotWidth - x1, Math.abs(y2 - y1));
    }
  }

  if (o.supportResistance) {
    for (const lvl of s.levels.slice(0, 10)) {
      if (lvl.broken) continue;
      const y = priceY(lvl.price, layout.mainTop, layout.mainH);
      r.setStrokeStyle(lvl.kind === "support" ? theme.bullish : theme.bearish);
      r.setLineDash([3, 3]);
      r.setLineWidth(1);
      r.beginPath();
      r.moveTo(0, y);
      r.lineTo(layout.plotWidth, y);
      r.stroke();
      r.setLineDash([]);
      r.setFillStyle(theme.text);
      r.setFont(theme.fontSmall);
      r.fillText(
        `${lvl.kind === "support" ? "S" : "R"} ${formatPriceLabel(lvl.price)}`,
        4,
        y - 2,
      );
    }
  }

  if (o.liquidity) {
    for (const liq of s.liquidity.slice(0, 12)) {
      const y = priceY(liq.price, layout.mainTop, layout.mainH);
      r.setStrokeStyle("rgba(168,85,247,0.7)");
      r.setLineDash([2, 2]);
      r.beginPath();
      r.moveTo(0, y);
      r.lineTo(layout.plotWidth, y);
      r.stroke();
      r.setLineDash([]);
    }
  }

  if (o.premiumDiscount && s.premiumDiscount) {
    const pd = s.premiumDiscount;
    const yEq = priceY(pd.equilibrium, layout.mainTop, layout.mainH);
    r.setStrokeStyle(theme.crosshair);
    r.setLineDash([6, 4]);
    r.beginPath();
    r.moveTo(0, yEq);
    r.lineTo(layout.plotWidth, yEq);
    r.stroke();
    r.setLineDash([]);
    r.setFillStyle("rgba(255,107,0,0.06)");
    const yPh = priceY(pd.premiumHigh, layout.mainTop, layout.mainH);
    const yPl = priceY(pd.premiumLow, layout.mainTop, layout.mainH);
    r.fillRect(0, Math.min(yPh, yPl), layout.plotWidth, Math.abs(yPh - yPl));
    r.setFillStyle("rgba(0,212,106,0.06)");
    const yDh = priceY(pd.discountHigh, layout.mainTop, layout.mainH);
    const yDl = priceY(pd.discountLow, layout.mainTop, layout.mainH);
    r.fillRect(0, Math.min(yDh, yDl), layout.plotWidth, Math.abs(yDh - yDl));
  }

  if (o.structure || o.swings) {
    for (const sw of s.swings.slice(-20)) {
      if (!o.swings) break;
      const x = viewport.indexToX(sw.index + 0.5, layout.plotLeft, layout.plotWidth);
      const y = priceY(sw.price, layout.mainTop, layout.mainH);
      r.setFillStyle(sw.kind === "high" ? theme.bearish : theme.bullish);
      r.beginPath();
      r.arc(x, y, 3, 0, Math.PI * 2);
      r.fill();
    }
    if (o.structure) {
      for (const st of s.structure.slice(-16)) {
        const x = viewport.indexToX(st.index + 0.5, layout.plotLeft, layout.plotWidth);
        const y = priceY(st.price, layout.mainTop, layout.mainH);
        r.setFillStyle(st.direction === "bullish" ? theme.bullish : theme.bearish);
        r.setFont(theme.fontSmall);
        r.fillText(st.label, x + 4, y - 4);
      }
    }
  }

  if (o.trend) {
    r.setFillStyle(theme.textBright);
    r.setFont(theme.font);
    const label = `Trend: ${s.trend.classification.replace(/_/g, " ")} (${Math.round(s.trend.confidence)}%)`;
    r.fillText(label, 8, layout.mainTop + 14);
  }

  if (o.patterns) {
    for (const p of s.patterns.slice(-4)) {
      const x = viewport.indexToX(p.endIndex + 0.5, layout.plotLeft, layout.plotWidth);
      r.setFillStyle(theme.crosshair);
      r.setFont(theme.fontSmall);
      r.fillText(p.kind.replace(/_/g, " "), Math.min(x, layout.plotWidth - 80), layout.mainTop + 28);
    }
  }

  void candleTimeSec;
}
