"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { Candlestick } from "../../types";
import { useIntelligenceStore } from "../../intelligence/store/intelligence-store";
import { useDecisionStore } from "../../decision-engine/store/decision-store";
import { useChartUiStore } from "../../store/ui-store";
import { useChartStore } from "../../store/chart-store";
import { useIndicatorStore } from "../../store/indicator-store";
import { useDrawingStore } from "../../store/drawing-store";
import { useViewportStore } from "../../store/viewport-store";
import { buildAthenaContext } from "../context/builder";
import { getCopilotService } from "../services/CopilotService";
import { useCopilotStore } from "../store/copilot-store";
import { suggestQuestions } from "../utils/suggestions";
import type {
  QuickActionId,
  SummaryHorizon,
  ExplainTarget,
} from "../types";
import { uid } from "../utils/id";
import { getNewsContext } from "@/services/news";

export function useCopilot(candles: Candlestick[]) {
  const symbol = useChartStore((s) => s.symbol);
  const timeframe = useChartStore((s) => s.timeframe);
  const analysis = useIntelligenceStore((s) => s.snapshot);
  const opportunity = useDecisionStore((s) => s.opportunity);
  const decisionEvents = useDecisionStore((s) => s.events);
  const smartCursor = useChartUiStore((s) => s.smartCursor);
  const hoverPrice = useChartUiStore((s) => s.hoverPrice);
  const flags = useIndicatorStore((s) => s.flags);
  const selectedIds = useDrawingStore((s) => s.selectedIds);
  const viewportFrom = useViewportStore((s) => s.from);
  const viewportTo = useViewportStore((s) => s.to);

  const selectedObject = useCopilotStore((s) => s.selectedObject);
  const settings = useCopilotStore((s) => s.settings);
  const messages = useCopilotStore((s) => s.messages);
  const pushMessage = useCopilotStore((s) => s.pushMessage);
  const setBusy = useCopilotStore((s) => s.setBusy);
  const setError = useCopilotStore((s) => s.setError);
  const setLastInsights = useCopilotStore((s) => s.setLastInsights);
  const setJournalDraft = useCopilotStore((s) => s.setJournalDraft);
  const loadConversation = useCopilotStore((s) => s.loadConversation);

  const [news, setNews] = useState<Array<{ title: string; impact: string }>>([]);

  useEffect(() => {
    let cancelled = false;
    void getNewsContext(symbol)
      .then((n) => {
        if (cancelled) return;
        const fromEvents = (n.upcomingEvents ?? []).slice(0, 3).map((e) => ({
          title: e.title,
          impact: e.impact,
        }));
        const fromHeadlines = (n.headlines ?? []).slice(0, 3).map((title) => ({
          title,
          impact: n.highImpactUpcoming ? "high" : "medium",
        }));
        setNews(fromEvents.length ? fromEvents : fromHeadlines);
      })
      .catch(() => {
        if (!cancelled) setNews([]);
      });
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  const openIndicators = useMemo(
    () =>
      Object.entries(flags)
        .filter(([, v]) => v)
        .map(([k]) => k),
    [flags],
  );

  const ctx = useMemo(
    () =>
      buildAthenaContext({
        analysis,
        opportunity,
        candles,
        awareness: {
          symbol,
          timeframe,
          selectedCandleTime: smartCursor?.timeSec
            ? new Date(smartCursor.timeSec * 1000).toISOString()
            : null,
          hoverPrice,
          selectedDrawingIds: selectedIds,
          openIndicators,
          zoomBars: Math.max(1, viewportTo - viewportFrom),
          selectedTradeId: null,
        },
        selectedObject,
        recentDecisionLabels: decisionEvents.slice(-8).map((e) => e.label),
        news,
      }),
    [
      analysis,
      opportunity,
      candles,
      symbol,
      timeframe,
      smartCursor,
      hoverPrice,
      selectedIds,
      openIndicators,
      viewportFrom,
      viewportTo,
      selectedObject,
      decisionEvents,
      news,
    ],
  );

  const suggestions = useMemo(() => suggestQuestions(ctx), [ctx]);

  const ensureThread = useCallback(() => {
    loadConversation(symbol, timeframe, null);
  }, [loadConversation, symbol, timeframe]);

  const ask = useCallback(
    async (question: string) => {
      ensureThread();
      const userMsg = {
        id: uid("msg"),
        role: "user" as const,
        content: question,
        createdAt: Date.now(),
      };
      pushMessage(userMsg);
      setBusy(true);
      setError(null);
      try {
        const reply = await getCopilotService().ask(
          ctx,
          question,
          settings.provider,
          [...messages, userMsg],
        );
        pushMessage(reply);
        setLastInsights(reply.content);
        if (question.toLowerCase().includes("journal")) {
          setJournalDraft(reply.content);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Copilot failed");
      } finally {
        setBusy(false);
      }
    },
    [
      ensureThread,
      pushMessage,
      setBusy,
      setError,
      ctx,
      settings.provider,
      messages,
      setLastInsights,
      setJournalDraft,
    ],
  );

  const runQuick = useCallback(
    async (action: QuickActionId) => {
      ensureThread();
      pushMessage({
        id: uid("msg"),
        role: "user",
        content: `[Quick] ${action.replace(/_/g, " ")}`,
        createdAt: Date.now(),
        meta: { action },
      });
      setBusy(true);
      try {
        const reply = await getCopilotService().quickAction(
          ctx,
          action,
          settings.provider,
          messages,
        );
        pushMessage(reply);
        setLastInsights(reply.content);
        if (action === "generate_journal") setJournalDraft(reply.content);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Quick action failed");
      } finally {
        setBusy(false);
      }
    },
    [
      ensureThread,
      pushMessage,
      setBusy,
      ctx,
      settings.provider,
      messages,
      setLastInsights,
      setJournalDraft,
      setError,
    ],
  );

  const explainTarget = useCallback(
    async (target: ExplainTarget) => {
      useCopilotStore.getState().setSelectedObject(target);
      useCopilotStore.getState().setTab("chat");
      ensureThread();
      pushMessage({
        id: uid("msg"),
        role: "user",
        content: `Explain: ${target.kind} — ${target.label}`,
        createdAt: Date.now(),
        meta: { action: "click_explain" },
      });
      setBusy(true);
      try {
        const nextCtx = buildAthenaContext({
          analysis,
          opportunity,
          candles,
          awareness: ctx.awareness,
          selectedObject: target,
          recentDecisionLabels: ctx.recentDecisions,
        });
        const reply = await getCopilotService().explainClick(
          nextCtx,
          settings.provider,
        );
        pushMessage(reply);
        setLastInsights(reply.content);
      } finally {
        setBusy(false);
      }
    },
    [
      ensureThread,
      pushMessage,
      setBusy,
      analysis,
      opportunity,
      candles,
      ctx.awareness,
      ctx.recentDecisions,
      settings.provider,
      setLastInsights,
    ],
  );

  const summarize = useCallback(
    async (horizon: SummaryHorizon) => {
      ensureThread();
      setBusy(true);
      try {
        const reply = await getCopilotService().summarize(
          ctx,
          horizon,
          settings.provider,
        );
        pushMessage({
          id: uid("msg"),
          role: "user",
          content: `Summarize (${horizon})`,
          createdAt: Date.now(),
        });
        pushMessage(reply);
        setLastInsights(reply.content);
      } finally {
        setBusy(false);
      }
    },
    [ensureThread, setBusy, ctx, settings.provider, pushMessage, setLastInsights],
  );

  const coach = useCallback(async () => {
    ensureThread();
    setBusy(true);
    try {
      const reply = await getCopilotService().coach(ctx, settings.provider);
      pushMessage({
        id: uid("msg"),
        role: "user",
        content: "Coach me on this setup",
        createdAt: Date.now(),
      });
      pushMessage(reply);
    } finally {
      setBusy(false);
    }
  }, [ensureThread, setBusy, ctx, settings.provider, pushMessage]);

  const review = useCallback(async () => {
    ensureThread();
    setBusy(true);
    try {
      const reply = await getCopilotService().review(ctx, settings.provider);
      pushMessage({
        id: uid("msg"),
        role: "user",
        content: "Review my trade",
        createdAt: Date.now(),
      });
      pushMessage(reply);
      setJournalDraft(reply.content);
    } finally {
      setBusy(false);
    }
  }, [ensureThread, setBusy, ctx, settings.provider, pushMessage, setJournalDraft]);

  return {
    ctx,
    suggestions,
    ask,
    runQuick,
    explainTarget,
    summarize,
    coach,
    review,
    ensureThread,
  };
}
