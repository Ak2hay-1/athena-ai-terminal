import type { ViewportState } from "../../types";

export class Viewport {
  from = 0;
  to = 100;
  minBars = 20;
  maxBars = 2500;

  get span(): number {
    return Math.max(1e-6, this.to - this.from);
  }

  clone(): ViewportState {
    return { from: this.from, to: this.to };
  }

  set(from: number, to: number, barCount: number): void {
    let f = from;
    let t = to;
    let span = t - f;
    if (span < this.minBars) {
      const mid = (f + t) / 2;
      f = mid - this.minBars / 2;
      t = mid + this.minBars / 2;
      span = this.minBars;
    }
    if (span > this.maxBars) {
      const mid = (f + t) / 2;
      f = mid - this.maxBars / 2;
      t = mid + this.maxBars / 2;
    }
    const pad = span * 0.05;
    const min = -pad;
    const max = barCount + pad;
    if (f < min) {
      t += min - f;
      f = min;
    }
    if (t > max) {
      f -= t - max;
      t = max;
    }
    this.from = f;
    this.to = t;
  }

  fit(barCount: number, visible = 120): void {
    if (barCount <= 0) {
      this.from = 0;
      this.to = visible;
      return;
    }
    const span = Math.min(barCount, Math.max(this.minBars, visible));
    this.from = Math.max(0, barCount - span);
    this.to = barCount;
  }

  pan(deltaBars: number, barCount: number): void {
    this.set(this.from + deltaBars, this.to + deltaBars, barCount);
  }

  zoomAt(anchorIndex: number, factor: number, barCount: number): void {
    const span = this.span;
    const newSpan = span * factor;
    const ratio = (anchorIndex - this.from) / span;
    const f = anchorIndex - newSpan * ratio;
    const t = f + newSpan;
    this.set(f, t, barCount);
  }

  indexToX(index: number, plotLeft: number, plotWidth: number): number {
    return plotLeft + ((index - this.from) / this.span) * plotWidth;
  }

  xToIndex(x: number, plotLeft: number, plotWidth: number): number {
    return this.from + ((x - plotLeft) / Math.max(1, plotWidth)) * this.span;
  }

  visibleRange(barCount: number): { start: number; end: number } {
    const start = Math.max(0, Math.floor(this.from) - 1);
    const end = Math.min(barCount, Math.ceil(this.to) + 1);
    return { start, end };
  }

  barsBeforeLeft(): number {
    return this.from;
  }
}
