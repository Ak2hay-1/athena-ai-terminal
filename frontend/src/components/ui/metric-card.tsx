import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "bullish" | "bearish" | "warning" | "ai" | "primary";
  className?: string;
}

const valueTone: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  default: "text-foreground",
  bullish: "text-bullish",
  bearish: "text-bearish",
  warning: "text-warning",
  ai: "text-ai",
  primary: "text-primary",
};

export function MetricCard({
  label,
  value,
  hint,
  tone = "default",
  className,
}: MetricCardProps) {
  return (
    <div className={cn("panel p-4", className)}>
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className={cn("mt-2 text-2xl font-semibold tracking-tight", valueTone[tone])}>
        {value}
      </p>
      {hint ? <p className="mt-1 text-xs text-muted">{hint}</p> : null}
    </div>
  );
}
