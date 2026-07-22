/**
 * Renderer abstraction — Canvas today, WebGL/Pixi later.
 * Layers must not import canvas APIs directly; use this interface.
 */
export interface IChartRenderer {
  readonly kind: "canvas" | "webgl";
  resize(cssWidth: number, cssHeight: number, dpr: number): void;
  clear(color: string): void;
  setFillStyle(style: string): void;
  setStrokeStyle(style: string): void;
  setLineWidth(width: number): void;
  setFont(font: string): void;
  setGlobalAlpha(alpha: number): void;
  setLineDash(segments: number[]): void;
  beginPath(): void;
  moveTo(x: number, y: number): void;
  lineTo(x: number, y: number): void;
  arc(x: number, y: number, r: number, start: number, end: number): void;
  closePath(): void;
  stroke(): void;
  fill(): void;
  fillRect(x: number, y: number, w: number, h: number): void;
  strokeRect(x: number, y: number, w: number, h: number): void;
  fillText(text: string, x: number, y: number): void;
  clipRect(x: number, y: number, w: number, h: number): void;
  save(): void;
  restore(): void;
  /** Export PNG data URL when supported (canvas). */
  toDataURL?(type?: string): string;
  /**
   * Escape hatch for canvas-only effects (gradients).
   * Returns null on non-canvas renderers.
   */
  getCanvas2D(): CanvasRenderingContext2D | null;
  getCanvasElement(): HTMLCanvasElement | null;
}

export interface RendererFactoryOptions {
  canvas: HTMLCanvasElement;
}
