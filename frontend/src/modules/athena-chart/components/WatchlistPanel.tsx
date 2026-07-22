"use client";

import { Star } from "lucide-react";
import { useWatchlistStore } from "../store/watchlist-store";
import { useChartStore } from "../store/chart-store";
import { cn } from "@/lib/utils";

export function WatchlistPanel() {
  const items = useWatchlistStore((s) => s.items);
  const query = useWatchlistStore((s) => s.query);
  const setQuery = useWatchlistStore((s) => s.setQuery);
  const toggleFavorite = useWatchlistStore((s) => s.toggleFavorite);
  const reorder = useWatchlistStore((s) => s.reorder);
  const setSymbol = useChartStore((s) => s.setSymbol);
  const symbol = useChartStore((s) => s.symbol);

  const filtered = items.filter(
    (i) => !query || i.symbol.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border p-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search pairs…"
          className="w-full rounded-sm border border-border bg-panel px-2 py-1.5 font-mono text-[11px] focus:border-primary/50 focus:outline-none"
        />
      </div>
      <div className="flex-1 overflow-y-auto">
        {filtered.map((item, idx) => (
          <div
            key={item.symbol}
            draggable
            onDragStart={(e) => e.dataTransfer.setData("text/plain", String(idx))}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const from = Number(e.dataTransfer.getData("text/plain"));
              if (!Number.isNaN(from)) reorder(from, idx);
            }}
            onClick={() => setSymbol(item.symbol)}
            className={cn(
              "flex cursor-pointer items-center gap-2 border-b border-border-subtle px-2 py-2 hover:bg-panel",
              symbol === item.symbol && "bg-primary/10",
            )}
          >
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                toggleFavorite(item.symbol);
              }}
              className={item.favorite ? "text-primary" : "text-muted"}
            >
              <Star className="h-3 w-3" fill={item.favorite ? "currentColor" : "none"} />
            </button>
            <div className="min-w-0 flex-1">
              <div className="font-mono text-[11px] font-medium text-foreground">
                {item.symbol}
              </div>
              <div className="flex gap-2 font-mono text-[10px] text-muted">
                <span>{item.lastPrice.toFixed(item.lastPrice > 50 ? 2 : 5)}</span>
                <span
                  className={
                    item.dailyPct >= 0 ? "text-bullish" : "text-bearish"
                  }
                >
                  {item.dailyPct >= 0 ? "+" : ""}
                  {item.dailyPct.toFixed(2)}%
                </span>
                <span>spr —</span>
              </div>
            </div>
            <MiniSpark values={item.spark} up={item.dailyPct >= 0} />
          </div>
        ))}
      </div>
    </div>
  );
}

function MiniSpark({ values, up }: { values: number[]; up: boolean }) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(1e-9, max - min);
  const pts = values
    .map((v, i) => {
      const x = (i / Math.max(1, values.length - 1)) * 40;
      const y = 16 - ((v - min) / span) * 14;
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <svg width="40" height="16" className="shrink-0 opacity-80">
      <polyline
        fill="none"
        stroke={up ? "#00d46a" : "#ff4d4d"}
        strokeWidth="1"
        points={pts}
      />
    </svg>
  );
}
