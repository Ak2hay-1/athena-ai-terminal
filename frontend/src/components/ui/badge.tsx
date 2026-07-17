import * as React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: "default" | "bullish" | "bearish" | "warning" | "ai" | "neutral" | "primary";
}

const toneClasses: Record<NonNullable<BadgeProps["tone"]>, string> = {
  default: "bg-panel-elevated text-muted border-border",
  bullish: "bg-bullish/10 text-bullish border-bullish/25",
  bearish: "bg-bearish/10 text-bearish border-bearish/25",
  warning: "bg-warning/10 text-warning border-warning/25",
  ai: "bg-ai/10 text-ai border-ai/25",
  neutral: "bg-zinc-500/10 text-zinc-300 border-zinc-500/25",
  primary: "bg-primary/10 text-primary border-primary/25",
};

export function Badge({ className, tone = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide",
        toneClasses[tone],
        className,
      )}
      {...props}
    />
  );
}
