"use client";

import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Briefcase, LineChart, MessageSquare, Sparkles } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SignalBadge } from "@/components/ui/signal-badge";
import { priceDigitsFor } from "@/constants/markets";
import { formatPercent, formatPrice } from "@/lib/utils";
import { placeOrderFromRecommendation } from "@/services/trading";
import type { Recommendation, Signal, TimeframeSignalSnapshot } from "@/types";

interface RecommendationHeroCardProps {
  recommendation: Recommendation;
  /** Latest signal per timeframe — shows alignment without gating the hero. */
  timeframeSignals?: TimeframeSignalSnapshot[];
}

function signalStance(signal: Signal): string | null {
  if (signal === "NO_TRADE") {
    return "Blocked — risk gates failed. Do not enter.";
  }
  if (signal === "HOLD" || signal === "NEUTRAL") {
    return "Standby — stay flat and wait for the next setup.";
  }
  return null;
}

export function RecommendationHeroCard({
  recommendation,
  timeframeSignals = [],
}: RecommendationHeroCardProps) {
  const queryClient = useQueryClient();
  const [orderError, setOrderError] = useState<string | null>(null);
  const [orderSuccess, setOrderSuccess] = useState<string | null>(null);
  const isBuy = recommendation.signal.includes("BUY");
  const isSell = recommendation.signal.includes("SELL");
  const actionable = isBuy || isSell;
  const digits = priceDigitsFor(recommendation.symbol, recommendation.entry);
  const stance = signalStance(recommendation.signal);

  const orderMutation = useMutation({
    mutationFn: () => placeOrderFromRecommendation(recommendation),
    onSuccess: (result) => {
      if (!result.success) {
        setOrderSuccess(null);
        setOrderError(result.reasons?.join(" ") ?? "Order rejected.");
        return;
      }
      setOrderError(null);
      const trade = result.trade;
      const ticket = trade?.ticket;
      const orderType = String(trade?.order_type ?? "LIMIT").toUpperCase();
      const status = String(trade?.status ?? "").toUpperCase();
      setOrderSuccess(
        ticket
          ? `MT5 ${orderType} placed — ticket #${ticket}${status ? ` (${status})` : ""}`
          : `MT5 ${orderType} order placed.`,
      );
      void queryClient.invalidateQueries({ queryKey: ["trade", "positions"] });
    },
    onError: (error) => {
      setOrderSuccess(null);
      setOrderError(
        error instanceof Error ? error.message : "Failed to execute trade.",
      );
    },
  });

  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="relative overflow-hidden rounded-sm border border-border bg-panel p-4"
    >
      <div
        className={`pointer-events-none absolute inset-y-0 left-0 w-1 ${
          isBuy ? "bg-bullish" : isSell ? "bg-bearish" : "bg-primary"
        }`}
      />

      <div className="relative flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="ai">Best overall setup</Badge>
            <Badge tone="primary">{recommendation.symbol}</Badge>
            <Badge tone="default">Setup · {recommendation.timeframe}</Badge>
          </div>
          <div className="mt-3 flex flex-wrap items-end gap-4">
            <h2
              className={`text-3xl font-semibold tracking-tight ${
                isBuy ? "text-bullish" : isSell ? "text-bearish" : "text-ai"
              }`}
            >
              {recommendation.signal === "HOLD"
                ? "Standby (HOLD)"
                : recommendation.signal === "NO_TRADE"
                  ? "Blocked (NO TRADE)"
                  : recommendation.signal.replace("_", " ")}
            </h2>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                Confidence
              </p>
              <p className="text-2xl font-semibold text-foreground tabular-nums">
                {formatPercent(recommendation.confidence)}
              </p>
            </div>
          </div>
          {stance ? (
            <p className="mt-2 max-w-xl text-xs text-muted">{stance}</p>
          ) : (
            <p className="mt-2 max-w-xl text-xs text-muted">
              Athena picks the strongest actionable setup across timeframes — chart
              TF is for viewing price only.
            </p>
          )}
        </div>
        <SignalBadge signal={recommendation.signal} className="text-sm px-3 py-1" />
      </div>

      {timeframeSignals.length > 0 ? (
        <div className="relative mt-4">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Multi-timeframe alignment
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {timeframeSignals.map((snap) => {
              const isBest =
                snap.timeframe.toUpperCase() ===
                recommendation.timeframe.toUpperCase();
              const snapBuy = snap.signal.includes("BUY");
              const snapSell = snap.signal.includes("SELL");
              return (
                <div
                  key={snap.timeframe}
                  className={`rounded-sm border px-2 py-1 font-mono text-[11px] tabular-nums ${
                    isBest
                      ? "border-primary/50 bg-primary/10 text-foreground"
                      : "border-border/70 bg-background/30 text-muted"
                  }`}
                  title={`${snap.timeframe} · ${snap.signal} · ${snap.confidence}%`}
                >
                  <span className="mr-1.5 text-muted-foreground">{snap.timeframe}</span>
                  <span
                    className={
                      snapBuy
                        ? "text-bullish"
                        : snapSell
                          ? "text-bearish"
                          : "text-muted-foreground"
                    }
                  >
                    {snap.signal.replace("_", " ")}
                  </span>
                  <span className="ml-1 text-muted-foreground">
                    {snap.confidence}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      <div className="relative mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <Meta
          label="Trend"
          value={recommendation.trend}
          tone={
            recommendation.trend === "Bullish"
              ? "bullish"
              : recommendation.trend === "Bearish"
                ? "bearish"
                : "default"
          }
        />
        <Meta
          label="Risk"
          value={recommendation.risk}
          tone={
            recommendation.risk === "Low"
              ? "bullish"
              : recommendation.risk === "High"
                ? "bearish"
                : "warning"
          }
        />
        <Meta
          label="Entry"
          value={`${formatPrice(recommendation.entry, digits)}${
            recommendation.entryType && recommendation.entryType !== "NONE"
              ? ` · ${recommendation.entryType}`
              : ""
          }`}
        />
        <Meta
          label="Risk / Reward"
          value={`${recommendation.riskReward.toFixed(1)}x`}
          tone="primary"
        />
        <Meta
          label="Stop Loss"
          value={formatPrice(recommendation.stopLoss, digits)}
          tone="bearish"
        />
        <Meta
          label="Take Profit"
          value={formatPrice(recommendation.takeProfit, digits)}
          tone="bullish"
        />
      </div>

      {(recommendation.slReason || recommendation.tpReason) && (
        <div className="relative mt-3 grid gap-2 text-xs text-muted sm:grid-cols-2">
          {recommendation.slReason ? <p>SL: {recommendation.slReason}</p> : null}
          {recommendation.tpReason ? <p>TP: {recommendation.tpReason}</p> : null}
        </div>
      )}

      {recommendation.reasons.length > 0 ? (
        <div className="relative mt-4">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Reasoning
          </p>
          <ul className="mt-2 grid gap-2 sm:grid-cols-2">
            {recommendation.reasons.map((reason, index) => (
              <li
                key={`${index}-${reason}`}
                className="flex items-center gap-2 rounded-sm border border-border/80 bg-background/40 px-3 py-2 text-sm text-zinc-300"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-ai" />
                {reason}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {orderError ? (
        <p className="relative mt-3 text-xs text-bearish">{orderError}</p>
      ) : null}
      {orderSuccess ? (
        <p className="relative mt-3 text-xs text-bullish">{orderSuccess}</p>
      ) : null}

      <div className="relative mt-4 flex flex-wrap gap-2">
        <Button
          variant={actionable ? "bullish" : "secondary"}
          disabled={!actionable || orderMutation.isPending}
          onClick={() => {
            setOrderError(null);
            setOrderSuccess(null);
            orderMutation.mutate();
          }}
          title={
            actionable
              ? "Place an MT5 limit order at entry (or market if price already passed) with SL/TP"
              : "Only BUY/SELL signals can execute trades"
          }
        >
          <Briefcase className="h-3.5 w-3.5" />
          {orderMutation.isPending ? "Executing…" : "Execute trade"}
        </Button>
        <Button variant="ai" asChild>
          <Link
            href={
              recommendation.id
                ? `/recommendations/${recommendation.id}`
                : `/ai?q=${encodeURIComponent(`Explain the current ${recommendation.symbol} ${recommendation.timeframe} recommendation`)}`
            }
          >
            <Sparkles className="h-3.5 w-3.5" />
            Explain
          </Link>
        </Button>
        <Button variant="secondary" asChild>
          <Link href={`/markets/${recommendation.symbol.toLowerCase()}`}>
            <LineChart className="h-3.5 w-3.5" />
            View Chart
          </Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/ai">
            <MessageSquare className="h-3.5 w-3.5" />
            Ask Athena
          </Link>
        </Button>
      </div>
    </motion.section>
  );
}

function Meta({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "bullish" | "bearish" | "warning" | "primary";
}) {
  const toneClass = {
    default: "text-foreground",
    bullish: "text-bullish",
    bearish: "text-bearish",
    warning: "text-warning",
    primary: "text-primary",
  }[tone];

  return (
    <div className="rounded-sm border border-border/70 bg-background/30 px-3 py-2">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className={`mt-1 text-sm font-semibold tabular-nums ${toneClass}`}>
        {value}
      </p>
    </div>
  );
}
