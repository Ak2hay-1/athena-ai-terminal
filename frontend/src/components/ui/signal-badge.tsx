import { cn } from "@/lib/utils";
import type { Signal } from "@/types";

const signalTone: Record<
  Signal,
  { label: string; className: string; title: string }
> = {
  STRONG_BUY: {
    label: "Strong Buy",
    className: "bg-bullish/15 text-bullish border-bullish/30",
    title: "High-conviction long bias",
  },
  BUY: {
    label: "Buy",
    className: "bg-bullish/10 text-bullish border-bullish/25",
    title: "Actionable long plan",
  },
  NEUTRAL: {
    label: "Neutral",
    className: "bg-zinc-500/10 text-zinc-300 border-zinc-500/25",
    title: "No directional edge — stay flat",
  },
  HOLD: {
    label: "Standby",
    className: "bg-zinc-500/10 text-zinc-300 border-zinc-500/25",
    title: "Standby (HOLD) — stay flat and wait for the next setup",
  },
  NO_TRADE: {
    label: "No Trade",
    className: "bg-warning/10 text-warning border-warning/25",
    title:
      "Blocked (NO TRADE) — risk gates failed (news, sideways, invalid SL, etc.)",
  },
  SELL: {
    label: "Sell",
    className: "bg-bearish/10 text-bearish border-bearish/25",
    title: "Actionable short plan",
  },
  STRONG_SELL: {
    label: "Strong Sell",
    className: "bg-bearish/15 text-bearish border-bearish/30",
    title: "High-conviction short bias",
  },
};

export function SignalBadge({
  signal,
  className,
}: {
  signal: Signal;
  className?: string;
}) {
  const config = signalTone[signal] ?? signalTone.HOLD;
  return (
    <span
      title={config.title}
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold",
        config.className,
        className,
      )}
    >
      {config.label}
    </span>
  );
}
