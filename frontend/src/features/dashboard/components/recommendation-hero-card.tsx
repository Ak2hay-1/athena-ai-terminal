"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { MessageSquare, LineChart, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SignalBadge } from "@/components/ui/signal-badge";
import { priceDigitsFor } from "@/constants/markets";
import { formatPercent, formatPrice } from "@/lib/utils";
import type { Recommendation } from "@/types";

interface RecommendationHeroCardProps {
  recommendation: Recommendation;
}

export function RecommendationHeroCard({
  recommendation,
}: RecommendationHeroCardProps) {
  const isBuy = recommendation.signal.includes("BUY");
  const isSell = recommendation.signal.includes("SELL");
  const digits = priceDigitsFor(recommendation.symbol, recommendation.entry);

  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="relative overflow-hidden rounded-sm border border-border bg-panel p-5"
    >
      <div
        className={`pointer-events-none absolute inset-y-0 left-0 w-1 ${
          isBuy ? "bg-bullish" : isSell ? "bg-bearish" : "bg-primary"
        }`}
      />

      <div className="relative flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="ai">AI Recommendation</Badge>
            <Badge tone="primary">{recommendation.symbol}</Badge>
            <Badge tone="default">{recommendation.timeframe}</Badge>
          </div>
          <div className="mt-4 flex flex-wrap items-end gap-4">
            <h2
              className={`text-4xl font-semibold tracking-tight ${
                isBuy ? "text-bullish" : isSell ? "text-bearish" : "text-ai"
              }`}
            >
              {recommendation.signal.replace("_", " ")}
            </h2>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                Confidence
              </p>
              <p className="text-3xl font-semibold text-foreground">
                {formatPercent(recommendation.confidence)}
              </p>
            </div>
          </div>
        </div>
        <SignalBadge signal={recommendation.signal} className="text-sm px-3 py-1" />
      </div>

      <div className="relative mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Meta label="Trend" value={recommendation.trend} tone={recommendation.trend === "Bullish" ? "bullish" : recommendation.trend === "Bearish" ? "bearish" : "default"} />
        <Meta label="Risk" value={recommendation.risk} tone={recommendation.risk === "Low" ? "bullish" : recommendation.risk === "High" ? "bearish" : "warning"} />
        <Meta
          label="Entry"
          value={`${formatPrice(recommendation.entry, digits)}${
            recommendation.entryType && recommendation.entryType !== "NONE"
              ? ` · ${recommendation.entryType}`
              : ""
          }`}
        />
        <Meta label="Risk / Reward" value={`${recommendation.riskReward.toFixed(1)}x`} tone="primary" />
        <Meta label="Stop Loss" value={formatPrice(recommendation.stopLoss, digits)} tone="bearish" />
        <Meta label="Take Profit" value={formatPrice(recommendation.takeProfit, digits)} tone="bullish" />
      </div>

      {(recommendation.slReason || recommendation.tpReason) && (
        <div className="relative mt-4 grid gap-2 text-xs text-muted sm:grid-cols-2">
          {recommendation.slReason ? <p>SL: {recommendation.slReason}</p> : null}
          {recommendation.tpReason ? <p>TP: {recommendation.tpReason}</p> : null}
        </div>
      )}

      <div className="relative mt-6">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Reasoning
        </p>
        <ul className="mt-2 grid gap-2 sm:grid-cols-2">
          {recommendation.reasons.map((reason) => (
            <li
              key={reason}
              className="flex items-center gap-2 rounded-lg border border-border/80 bg-background/40 px-3 py-2 text-sm text-zinc-300"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-ai" />
              {reason}
            </li>
          ))}
        </ul>
      </div>

      <div className="relative mt-6 flex flex-wrap gap-2">
        <Button variant="ai">
          <Sparkles className="h-3.5 w-3.5" />
          Explain
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
    <div className="rounded-lg border border-border/70 bg-background/30 px-3 py-2.5">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className={`mt-1 text-sm font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}
