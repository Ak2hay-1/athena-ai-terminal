"use client";

import { useEffect } from "react";
import type { Candlestick } from "../../types";
import { getIntelligenceService } from "../services/IntelligenceService";
import { useIntelligenceStore } from "../store/intelligence-store";

/** Runs intelligence pipeline on candle changes (worker when available). */
export function useIntelligenceAnalysis(
  candles: Candlestick[],
  symbol: string,
  timeframe: string,
) {
  const settings = useIntelligenceStore((s) => s.settings);
  const setSnapshot = useIntelligenceStore((s) => s.setSnapshot);
  const setAnalyzing = useIntelligenceStore((s) => s.setAnalyzing);
  const setError = useIntelligenceStore((s) => s.setError);

  useEffect(() => {
    if (!candles.length) return;
    const svc = getIntelligenceService();
    svc.setHandlers({
      onResult: (snap) => {
        setSnapshot(snap);
        setAnalyzing(false);
        setError(null);
      },
      onError: (msg) => {
        setError(msg);
        setAnalyzing(false);
      },
    });
    setAnalyzing(true);
    svc.analyze({ candles, symbol, timeframe, settings });
  }, [candles, symbol, timeframe, settings, setSnapshot, setAnalyzing, setError]);
}
