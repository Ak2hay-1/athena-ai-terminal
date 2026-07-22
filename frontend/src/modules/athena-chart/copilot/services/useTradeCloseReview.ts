"use client";

import { useEffect, useRef } from "react";
import { useDecisionStore } from "../../decision-engine/store/decision-store";
import { useCopilotStore } from "../store/copilot-store";
import { getCopilotService } from "../services/CopilotService";
import { buildAthenaContext } from "../context/builder";
import { useIntelligenceStore } from "../../intelligence/store/intelligence-store";
import { useChartStore } from "../../store/chart-store";
import { uid } from "../utils/id";

/**
 * When Decision Engine marks a trade closed, request a grounded AI review once.
 * Cost-gated — not per candle.
 */
export function useTradeCloseReview(candlesLength: number) {
  const status = useDecisionStore((s) => s.opportunity?.status);
  const opportunity = useDecisionStore((s) => s.opportunity);
  const analysis = useIntelligenceStore((s) => s.snapshot);
  const symbol = useChartStore((s) => s.symbol);
  const timeframe = useChartStore((s) => s.timeframe);
  const provider = useCopilotStore((s) => s.settings.provider);
  const pushMessage = useCopilotStore((s) => s.pushMessage);
  const setJournalDraft = useCopilotStore((s) => s.setJournalDraft);
  const prev = useRef<string | null>(null);

  useEffect(() => {
    if (!opportunity || !analysis || !candlesLength) return;
    const key = `${opportunity.id}:${status}`;
    if (status === "closed" && prev.current !== key) {
      prev.current = key;
      const ctx = buildAthenaContext({
        analysis,
        opportunity,
        candles: [],
        awareness: { symbol, timeframe },
        recentDecisionLabels: [],
      });
      void getCopilotService()
        .review(ctx, provider)
        .then((reply) => {
          pushMessage({
            id: uid("msg"),
            role: "user",
            content: "Trade closed — auto review",
            createdAt: Date.now(),
          });
          pushMessage(reply);
          setJournalDraft(reply.content);
        });
    }
    if (status && status !== "closed") prev.current = key;
  }, [
    status,
    opportunity,
    analysis,
    candlesLength,
    symbol,
    timeframe,
    provider,
    pushMessage,
    setJournalDraft,
  ]);
}
