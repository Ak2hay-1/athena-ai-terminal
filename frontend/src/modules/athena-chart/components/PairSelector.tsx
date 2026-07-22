"use client";

import { useEffect } from "react";
import { useChartStore } from "../store/chart-store";
import { LIVE_CHART_TIMEFRAMES } from "../utils/timeframes";
import { SymbolSearchSelect } from "./SymbolSearchSelect";
import { cn } from "@/lib/utils";

export function PairSelector() {
  const symbol = useChartStore((s) => s.symbol);
  const setSymbol = useChartStore((s) => s.setSymbol);

  return (
    <SymbolSearchSelect
      value={symbol}
      onChange={setSymbol}
      aria-label="Pair"
    />
  );
}

export function TimeframeSelector() {
  const timeframe = useChartStore((s) => s.timeframe);
  const setTimeframe = useChartStore((s) => s.setTimeframe);
  const primary = ["1M", "5M", "15M", "1H", "4H", "D1"] as const;

  useEffect(() => {
    if (!(LIVE_CHART_TIMEFRAMES as readonly string[]).includes(timeframe)) {
      setTimeframe("5M");
    }
  }, [timeframe, setTimeframe]);

  const selected = (LIVE_CHART_TIMEFRAMES as readonly string[]).includes(
    timeframe,
  )
    ? timeframe
    : "5M";

  return (
    <div className="flex items-center gap-0.5">
      {primary.map((tf) => (
        <button
          key={tf}
          type="button"
          onClick={() => setTimeframe(tf)}
          className={cn(
            "h-7 rounded-sm border px-1.5 font-mono text-[10px] uppercase tracking-wide",
            selected === tf
              ? "border-primary/40 bg-primary/10 text-primary"
              : "border-border text-muted hover:text-foreground",
          )}
        >
          {tf}
        </button>
      ))}
      <select
        aria-label="More timeframes"
        value={selected}
        onChange={(e) => setTimeframe(e.target.value)}
        className="h-7 rounded-sm border border-border bg-panel px-1 font-mono text-[10px] text-foreground focus:border-primary/50 focus:outline-none"
      >
        {LIVE_CHART_TIMEFRAMES.map((tf) => (
          <option key={tf} value={tf}>
            {tf}
          </option>
        ))}
      </select>
    </div>
  );
}
