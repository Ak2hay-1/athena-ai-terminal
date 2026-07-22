"use client";

import { useEffect, useRef } from "react";
import { useDecisionStore } from "../../athena-chart/decision-engine/store/decision-store";
import { useAuthStore } from "@/store/auth-store";
import { getLearningEngine } from "../services/LearningEngine";
import { opportunityToTradeRecord } from "../services/intake";
import { useLearningStore } from "../store/learning-store";

/**
 * When Decision Engine closes/stops an opportunity, ingest into Learning Engine.
 * Runs in background — never blocks chart UI.
 */
export function useLearningIntake() {
  const user = useAuthStore((s) => s.user);
  const userId = user ? String(user.id) : "anonymous";
  const opportunity = useDecisionStore((s) => s.opportunity);
  const strategy = useDecisionStore((s) => s.settings.strategy);
  const riskMode = useDecisionStore((s) => s.settings.riskMode);
  const setUserId = useLearningStore((s) => s.setUserId);
  const refresh = useLearningStore((s) => s.refresh);
  const seen = useRef<string | null>(null);

  useEffect(() => {
    setUserId(userId);
  }, [userId, setUserId]);

  useEffect(() => {
    if (!opportunity) return;
    const key = `${opportunity.id}:${opportunity.status}`;
    if (
      opportunity.status !== "closed" &&
      opportunity.status !== "stopped" &&
      opportunity.status !== "cancelled"
    ) {
      return;
    }
    if (seen.current === key) return;
    seen.current = key;

    const record = opportunityToTradeRecord(userId, opportunity, {
      strategy,
      riskMode,
    });
    if (!record) return;

    const run = () => {
      getLearningEngine(userId).recordTrade(record);
      refresh();
    };
    if (typeof requestIdleCallback !== "undefined") {
      requestIdleCallback(() => run());
    } else {
      setTimeout(run, 0);
    }
  }, [opportunity, userId, strategy, riskMode, refresh]);
}
