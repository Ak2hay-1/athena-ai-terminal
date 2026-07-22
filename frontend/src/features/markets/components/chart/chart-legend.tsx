"use client";

import type { Candle } from "@/types";

interface Props {
  candle: Candle | null;
  extras?: Array<{ label: string; value: string; color?: string }>;
}

export function ChartLegend({ candle, extras = [] }: Props) {
  if (!candle) {
    return (
      <div className="pointer-events-none absolute left-2 top-2 z-10 rounded-sm bg-black/50 px-2 py-1 font-mono text-[10px] text-muted-foreground">
        Crosshair for OHLC
      </div>
    );
  }

  const up = candle.close >= candle.open;
  return (
    <div className="pointer-events-none absolute left-2 top-2 z-10 max-w-[90%] rounded-sm bg-black/55 px-2 py-1 font-mono text-[10px] text-foreground/90">
      <span className="text-muted-foreground">O</span>{" "}
      {candle.open.toFixed(5)}{" "}
      <span className="text-muted-foreground">H</span>{" "}
      {candle.high.toFixed(5)}{" "}
      <span className="text-muted-foreground">L</span>{" "}
      {candle.low.toFixed(5)}{" "}
      <span className={up ? "text-bullish" : "text-bearish"}>
        C {candle.close.toFixed(5)}
      </span>{" "}
      <span className="text-muted-foreground">V</span> {candle.tick_volume}
      {extras.map((item) => (
        <span key={item.label} className="ml-2" style={{ color: item.color }}>
          {item.label} {item.value}
        </span>
      ))}
    </div>
  );
}
