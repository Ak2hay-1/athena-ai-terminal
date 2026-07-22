"use client";

import { useEffect, useRef } from "react";
import { ChartController } from "../engine/controller";
import type { EngineOptions } from "../types";

/** Bind a ChartController to a canvas element for the lifetime of the host. */
export function useChartEngine(
  canvasRef: React.RefObject<HTMLCanvasElement | null>,
  options: EngineOptions,
  deps: unknown[] = [],
) {
  const engineRef = useRef<ChartController | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const engine = new ChartController(canvasRef.current, options);
    engineRef.current = engine;
    return () => {
      engine.destroy();
      engineRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return engineRef;
}
