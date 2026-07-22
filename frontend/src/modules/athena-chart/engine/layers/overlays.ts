import {
  computeAtr,
  computeBollinger,
  computeEma,
  computeMacd,
  computeRsi,
  computeSma,
  computeVwap,
} from "../indicators";
import { RIGHT_AXIS, type PaintContext } from "./context";

function drawLineOverlay(
  ctx: PaintContext,
  values: Array<number | null>,
  start: number,
  end: number,
  color: string,
): void {
  const { r, layout, viewport, priceY } = ctx;
  r.setStrokeStyle(color);
  r.setLineWidth(1);
  r.beginPath();
  let started = false;
  for (let i = start; i < end; i++) {
    const v = values[i];
    if (v == null || !Number.isFinite(v)) {
      started = false;
      continue;
    }
    const x = viewport.indexToX(i + 0.5, layout.plotLeft, layout.plotWidth);
    const y = priceY(v, layout.mainTop, layout.mainH);
    if (!started) {
      r.moveTo(x, y);
      started = true;
    } else r.lineTo(x, y);
  }
  r.stroke();
}

export function drawOverlays(ctx: PaintContext, start: number, end: number): void {
  if (ctx.mode === "overview") return;
  const closes = ctx.candles.map((c) => c.close);
  const f = ctx.indicators;
  const { theme } = ctx;
  if (f.ema20) drawLineOverlay(ctx, computeEma(closes, 20), start, end, theme.ema20);
  if (f.ema50) drawLineOverlay(ctx, computeEma(closes, 50), start, end, theme.ema50);
  if (f.sma20) drawLineOverlay(ctx, computeSma(closes, 20), start, end, theme.sma20);
  if (f.sma50) drawLineOverlay(ctx, computeSma(closes, 50), start, end, theme.sma50);
  if (f.sma200) drawLineOverlay(ctx, computeSma(closes, 200), start, end, theme.sma200);
  if (f.bollinger) {
    const bb = computeBollinger(closes);
    drawLineOverlay(ctx, bb.upper, start, end, theme.bb);
    drawLineOverlay(ctx, bb.mid, start, end, theme.bb);
    drawLineOverlay(ctx, bb.lower, start, end, theme.bb);
  }
  if (f.vwap) drawLineOverlay(ctx, computeVwap(ctx.candles), start, end, theme.vwap);
  if (f.atr) drawLineOverlay(ctx, computeAtr(ctx.candles), start, end, theme.atr);
}

export function drawLevels(ctx: PaintContext): void {
  if (!ctx.levels) return;
  const { r, theme, layout, priceY, levels } = ctx;
  const lines: Array<{ p?: number; color: string; title: string }> = [
    { p: levels.entry, color: theme.entry, title: "Entry" },
    { p: levels.stopLoss, color: theme.stopLoss, title: "SL" },
    { p: levels.takeProfit, color: theme.takeProfit, title: "TP" },
  ];
  for (const line of lines) {
    if (!line.p || !Number.isFinite(line.p)) continue;
    const y = priceY(line.p, layout.mainTop, layout.mainH);
    r.setStrokeStyle(line.color);
    r.setLineDash([4, 3]);
    r.beginPath();
    r.moveTo(0, y);
    r.lineTo(layout.plotWidth, y);
    r.stroke();
    r.setLineDash([]);
    r.setFillStyle(line.color);
    r.setFont(theme.fontSmall);
    r.fillText(line.title, layout.plotWidth - 36, y - 4);
  }
}

export function drawRsiPane(ctx: PaintContext, start: number, end: number): void {
  const { r, theme, layout, candles, viewport, width } = ctx;
  const closes = candles.map((c) => c.close);
  const rsi = computeRsi(closes);
  r.setFillStyle(theme.background);
  r.fillRect(0, layout.rsiTop, layout.plotWidth + RIGHT_AXIS, layout.rsiH);
  r.setStrokeStyle(theme.border);
  r.beginPath();
  r.moveTo(0, layout.rsiTop);
  r.lineTo(width, layout.rsiTop);
  r.stroke();
  for (const level of [30, 70]) {
    const y = layout.rsiTop + ((100 - level) / 100) * layout.rsiH;
    r.setStrokeStyle(theme.grid);
    r.beginPath();
    r.moveTo(0, y);
    r.lineTo(layout.plotWidth, y);
    r.stroke();
  }
  r.setStrokeStyle(theme.rsi);
  r.beginPath();
  let started = false;
  for (let i = start; i < end; i++) {
    const v = rsi[i];
    if (v == null) {
      started = false;
      continue;
    }
    const x = viewport.indexToX(i + 0.5, layout.plotLeft, layout.plotWidth);
    const y = layout.rsiTop + ((100 - v) / 100) * layout.rsiH;
    if (!started) {
      r.moveTo(x, y);
      started = true;
    } else r.lineTo(x, y);
  }
  r.stroke();
  r.setFillStyle(theme.text);
  r.setFont(theme.fontSmall);
  r.fillText("RSI", 6, layout.rsiTop + 12);
}

export function drawMacdPane(ctx: PaintContext, start: number, end: number): void {
  const { r, theme, layout, candles, viewport, width } = ctx;
  const closes = candles.map((c) => c.close);
  const macd = computeMacd(closes);
  let min = 0;
  let max = 0;
  for (let i = start; i < end; i++) {
    const h = macd.hist[i];
    const m = macd.macd[i];
    const s = macd.signal[i];
    if (h != null) {
      min = Math.min(min, h);
      max = Math.max(max, h);
    }
    if (m != null) {
      min = Math.min(min, m);
      max = Math.max(max, m);
    }
    if (s != null) {
      min = Math.min(min, s);
      max = Math.max(max, s);
    }
  }
  const span = Math.max(1e-9, max - min);
  const yOf = (v: number) => layout.macdTop + ((max - v) / span) * layout.macdH;

  r.setFillStyle(theme.background);
  r.fillRect(0, layout.macdTop, layout.plotWidth + RIGHT_AXIS, layout.macdH);
  r.setStrokeStyle(theme.border);
  r.beginPath();
  r.moveTo(0, layout.macdTop);
  r.lineTo(width, layout.macdTop);
  r.stroke();

  const barW = Math.max(1, (layout.plotWidth / viewport.span) * 0.6);
  const zeroY = yOf(0);
  for (let i = start; i < end; i++) {
    const h = macd.hist[i];
    if (h == null) continue;
    const x = viewport.indexToX(i + 0.5, layout.plotLeft, layout.plotWidth);
    const y = yOf(h);
    r.setFillStyle(h >= 0 ? theme.volumeUp : theme.volumeDown);
    r.fillRect(x - barW / 2, Math.min(y, zeroY), barW, Math.max(1, Math.abs(y - zeroY)));
  }

  const strokeVals = (vals: Array<number | null>, color: string) => {
    r.setStrokeStyle(color);
    r.beginPath();
    let started = false;
    for (let i = start; i < end; i++) {
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
  strokeVals(macd.macd, theme.macd);
  strokeVals(macd.signal, theme.macdSignal);
  r.setFillStyle(theme.text);
  r.setFont(theme.fontSmall);
  r.fillText("MACD", 6, layout.macdTop + 12);
}
