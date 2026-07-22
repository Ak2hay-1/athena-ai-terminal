"use client";

import { MARKET_SYMBOLS, TIMEFRAMES } from "@/constants/markets";
import type { AutoTradeFilters } from "@/services/preferences";
import { cn } from "@/lib/utils";

interface AutoTradeFiltersFormProps {
  value: AutoTradeFilters;
  onChange: (next: AutoTradeFilters) => void;
  compact?: boolean;
  className?: string;
}

function toggleInList(list: string[], item: string): string[] {
  const upper = item.toUpperCase();
  if (list.includes(upper)) {
    return list.filter((x) => x !== upper);
  }
  return [...list, upper];
}

export function AutoTradeFiltersForm({
  value,
  onChange,
  compact = false,
  className,
}: AutoTradeFiltersFormProps) {
  return (
    <div className={cn("space-y-3", className)}>
      <p className="text-xs text-muted-foreground">
        Empty pairs/timeframes = all. Matching signals place orders directly on
        MT5 (not Athena paper positions).
      </p>

      <div>
        <p className="mb-1.5 text-xs font-medium text-muted">Pairs</p>
        <div
          className={cn(
            "flex flex-wrap gap-1.5",
            compact ? "max-h-24 overflow-y-auto" : "",
          )}
        >
          {MARKET_SYMBOLS.map((symbol) => {
            const selected = value.auto_trade_symbols.includes(symbol);
            return (
              <button
                key={symbol}
                type="button"
                onClick={() =>
                  onChange({
                    ...value,
                    auto_trade_symbols: toggleInList(
                      value.auto_trade_symbols,
                      symbol,
                    ),
                  })
                }
                className={cn(
                  "rounded-sm border px-2 py-0.5 font-mono text-[11px] transition-colors",
                  selected
                    ? "border-primary/50 bg-primary/15 text-foreground"
                    : "border-border bg-panel text-muted-foreground hover:border-primary/40",
                )}
              >
                {symbol}
              </button>
            );
          })}
        </div>
        {value.auto_trade_symbols.length > 0 ? (
          <button
            type="button"
            className="mt-1 text-[11px] text-muted-foreground underline-offset-2 hover:underline"
            onClick={() => onChange({ ...value, auto_trade_symbols: [] })}
          >
            Clear (use all pairs)
          </button>
        ) : (
          <p className="mt-1 text-[11px] text-muted-foreground">All pairs</p>
        )}
      </div>

      <div>
        <p className="mb-1.5 text-xs font-medium text-muted">Timeframes</p>
        <div className="flex flex-wrap gap-1.5">
          {TIMEFRAMES.map((tf) => {
            const selected = value.auto_trade_timeframes.includes(tf);
            return (
              <button
                key={tf}
                type="button"
                onClick={() =>
                  onChange({
                    ...value,
                    auto_trade_timeframes: toggleInList(
                      value.auto_trade_timeframes,
                      tf,
                    ),
                  })
                }
                className={cn(
                  "rounded-sm border px-2 py-0.5 font-mono text-[11px] transition-colors",
                  selected
                    ? "border-primary/50 bg-primary/15 text-foreground"
                    : "border-border bg-panel text-muted-foreground hover:border-primary/40",
                )}
              >
                {tf}
              </button>
            );
          })}
        </div>
        {value.auto_trade_timeframes.length > 0 ? (
          <button
            type="button"
            className="mt-1 text-[11px] text-muted-foreground underline-offset-2 hover:underline"
            onClick={() => onChange({ ...value, auto_trade_timeframes: [] })}
          >
            Clear (use all timeframes)
          </button>
        ) : (
          <p className="mt-1 text-[11px] text-muted-foreground">All timeframes</p>
        )}
      </div>

      <div className={cn("grid gap-3", compact ? "grid-cols-2" : "sm:grid-cols-2")}>
        <label className="block space-y-1 text-sm">
          <span className="text-xs text-muted">Min confidence %</span>
          <input
            type="number"
            min={0}
            max={100}
            value={value.auto_trade_min_confidence}
            onChange={(event) =>
              onChange({
                ...value,
                auto_trade_min_confidence: Number(event.target.value),
              })
            }
            className="h-8 w-full rounded-sm border border-border bg-panel px-2 font-mono text-sm outline-none focus:border-primary/50"
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="text-xs text-muted">Min confluence</span>
          <input
            type="number"
            min={0}
            max={100}
            value={value.auto_trade_min_confluence}
            onChange={(event) =>
              onChange({
                ...value,
                auto_trade_min_confluence: Number(event.target.value),
              })
            }
            className="h-8 w-full rounded-sm border border-border bg-panel px-2 font-mono text-sm outline-none focus:border-primary/50"
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="text-xs text-muted">Min R:R</span>
          <input
            type="number"
            min={0}
            step={0.1}
            value={value.auto_trade_min_rr}
            onChange={(event) =>
              onChange({
                ...value,
                auto_trade_min_rr: Number(event.target.value),
              })
            }
            className="h-8 w-full rounded-sm border border-border bg-panel px-2 font-mono text-sm outline-none focus:border-primary/50"
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="text-xs text-muted">Volume (lots)</span>
          <input
            type="number"
            min={0.01}
            max={100}
            step={0.01}
            value={value.auto_trade_volume}
            onChange={(event) =>
              onChange({
                ...value,
                auto_trade_volume: Number(event.target.value),
              })
            }
            className="h-8 w-full rounded-sm border border-border bg-panel px-2 font-mono text-sm outline-none focus:border-primary/50"
          />
        </label>
      </div>
    </div>
  );
}
