"use client";

import { useCallback, useEffect, useState } from "react";
import type { DrawingTool } from "./chart-indicators";

export type ChartDrawing =
  | {
      id: string;
      type: "trend" | "ray";
      t1: number;
      p1: number;
      t2: number;
      p2: number;
    }
  | {
      id: string;
      type: "hline";
      price: number;
    }
  | {
      id: string;
      type: "rect";
      t1: number;
      p1: number;
      t2: number;
      p2: number;
    }
  | {
      id: string;
      type: "fib";
      t1: number;
      p1: number;
      t2: number;
      p2: number;
    };

function storageKey(symbol: string, timeframe: string) {
  return `athena.chart.drawings:${symbol.toUpperCase()}:${timeframe.toUpperCase()}`;
}

export function useChartDrawings(symbol: string, timeframe: string) {
  const [drawings, setDrawings] = useState<ChartDrawing[]>([]);
  const [tool, setTool] = useState<DrawingTool>("cursor");
  const [magnet, setMagnet] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined" || !symbol || !timeframe) {
      setDrawings([]);
      return;
    }
    try {
      const raw = localStorage.getItem(storageKey(symbol, timeframe));
      if (!raw) {
        setDrawings([]);
        return;
      }
      const parsed = JSON.parse(raw) as ChartDrawing[];
      setDrawings(Array.isArray(parsed) ? parsed : []);
    } catch {
      setDrawings([]);
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    if (typeof window === "undefined" || !symbol || !timeframe) return;
    try {
      localStorage.setItem(
        storageKey(symbol, timeframe),
        JSON.stringify(drawings),
      );
    } catch {
      // ignore quota errors
    }
  }, [drawings, symbol, timeframe]);

  const addDrawing = useCallback((drawing: ChartDrawing) => {
    setDrawings((prev) => [...prev, drawing]);
  }, []);

  const clearDrawings = useCallback(() => {
    setDrawings([]);
  }, []);

  return {
    drawings,
    setDrawings,
    addDrawing,
    clearDrawings,
    tool,
    setTool,
    magnet,
    setMagnet,
  };
}
