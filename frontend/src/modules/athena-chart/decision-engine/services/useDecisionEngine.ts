"use client";

import { useEffect } from "react";
import type { Candlestick } from "../../types";
import { useIntelligenceStore } from "../../intelligence/store/intelligence-store";
import { getDecisionService } from "./DecisionService";
import { useDecisionStore } from "../store/decision-store";

/**
 * Runs decision pipeline when intelligence snapshot updates.
 * Consumes AnalysisSnapshot — does not re-run detectors.
 */
export function useDecisionEngine(
  candles: Candlestick[],
  symbol: string,
  timeframe: string,
) {
  const analysis = useIntelligenceStore((s) => s.snapshot);
  const settings = useDecisionStore((s) => s.settings);
  const previousOpportunity = useDecisionStore((s) => s.opportunity);
  const setSnapshot = useDecisionStore((s) => s.setSnapshot);
  const appendMemory = useDecisionStore((s) => s.appendMemory);
  const setDeciding = useDecisionStore((s) => s.setDeciding);
  const setError = useDecisionStore((s) => s.setError);

  useEffect(() => {
    if (!candles.length || !analysis) return;
    if (analysis.symbol !== symbol || analysis.timeframe !== timeframe) return;

    const svc = getDecisionService();
    svc.setHandlers({
      onResult: (snap, memory) => {
        setSnapshot(snap);
        if (memory.length) appendMemory(memory);
        setDeciding(false);
        setError(null);
      },
      onError: (msg) => {
        setError(msg);
        setDeciding(false);
      },
    });
    setDeciding(true);
    svc.decide({
      candles,
      symbol,
      timeframe,
      analysis,
      settings,
      previousOpportunity,
    });
  }, [
    candles,
    symbol,
    timeframe,
    analysis,
    settings,
    // only re-run when opp id/status changes meaningfully — avoid loops via updatedAt
    previousOpportunity?.id,
    previousOpportunity?.status,
    setSnapshot,
    appendMemory,
    setDeciding,
    setError,
  ]);
}
