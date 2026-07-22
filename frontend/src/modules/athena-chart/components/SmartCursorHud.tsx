"use client";

import { useChartStore } from "../store/chart-store";
import { useChartUiStore } from "../store/ui-store";
import {
  formatCrosshairTime,
  formatPriceLabel,
} from "../utils/format";

export function SmartCursorHud() {
  const smart = useChartUiStore((s) => s.smartCursor);
  const symbol = useChartStore((s) => s.symbol);
  if (!smart) return null;

  const { date, time } = formatCrosshairTime(smart.timeSec);

  return (
    <div className="pointer-events-none absolute left-2 top-2 z-20 rounded-sm border border-border/80 bg-black/70 px-2 py-1.5 font-mono text-[10px] text-foreground backdrop-blur-sm">
      <div className="flex flex-wrap gap-x-3 gap-y-0.5">
        <span>P {formatPriceLabel(smart.price, symbol)}</span>
        <span>
          {date} {time}
        </span>
        {smart.open != null ? (
          <span>O {formatPriceLabel(smart.open, symbol)}</span>
        ) : null}
        {smart.high != null ? (
          <span>H {formatPriceLabel(smart.high, symbol)}</span>
        ) : null}
        {smart.low != null ? (
          <span>L {formatPriceLabel(smart.low, symbol)}</span>
        ) : null}
        {smart.close != null ? (
          <span>C {formatPriceLabel(smart.close, symbol)}</span>
        ) : null}
        {smart.volume != null ? <span>V {smart.volume}</span> : null}
        {smart.pctChange != null ? (
          <span className={smart.pctChange >= 0 ? "text-bullish" : "text-bearish"}>
            {smart.pctChange >= 0 ? "+" : ""}
            {smart.pctChange.toFixed(3)}%
          </span>
        ) : null}
        <span className="text-muted">Spr —</span>
        <span className="text-muted">
          ATR{" "}
          {smart.atr != null ? formatPriceLabel(smart.atr, symbol) : "—"}
        </span>
      </div>
    </div>
  );
}
