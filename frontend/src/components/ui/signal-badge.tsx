import { cn } from "@/lib/utils";
import type { Signal } from "@/types";

const signalTone: Record<
  Signal,
  { label: string; className: string }
> = {
  STRONG_BUY: {
    label: "Strong Buy",
    className: "bg-bullish/15 text-bullish border-bullish/30",
  },
  BUY: {
    label: "Buy",
    className: "bg-bullish/10 text-bullish border-bullish/25",
  },
  NEUTRAL: {
    label: "Neutral",
    className: "bg-zinc-500/10 text-zinc-300 border-zinc-500/25",
  },
  HOLD: {
    label: "Hold",
    className: "bg-zinc-500/10 text-zinc-300 border-zinc-500/25",
  },
  NO_TRADE: {
    label: "No Trade",
    className: "bg-warning/10 text-warning border-warning/25",
  },
  SELL: {
    label: "Sell",
    className: "bg-bearish/10 text-bearish border-bearish/25",
  },
  STRONG_SELL: {
    label: "Strong Sell",
    className: "bg-bearish/15 text-bearish border-bearish/30",
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
