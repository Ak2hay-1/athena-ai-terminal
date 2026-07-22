/**
 * WebGL / PixiJS renderer stub.
 * Future: implement IChartRenderer without changing ChartController or layers' business logic.
 */
import type { IChartRenderer } from "../types";

export type WebGlRendererOptions = {
  canvas: HTMLCanvasElement;
};

export function isWebGlSupported(): boolean {
  if (typeof document === "undefined") return false;
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

/** Placeholder — throws until Pixi/WebGL backend is implemented. */
export function createWebGlRenderer(_options: WebGlRendererOptions): IChartRenderer {
  throw new Error(
    "WebGL renderer is not implemented yet. Use createCanvasRenderer().",
  );
}
