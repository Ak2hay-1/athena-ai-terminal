"use client";

import { listIndicatorPlugins } from "../engine/indicators/registry";
import { useIndicatorStore } from "../store/indicator-store";
import type { IndicatorFlags } from "../types";
import { cn } from "@/lib/utils";

export function IndicatorMenu() {
  const flags = useIndicatorStore((s) => s.flags);
  const menuOpen = useIndicatorStore((s) => s.menuOpen);
  const toggleFlag = useIndicatorStore((s) => s.toggleFlag);
  const setMenuOpen = useIndicatorStore((s) => s.setMenuOpen);
  const setPanelOpen = useIndicatorStore((s) => s.setPanelOpen);
  const addInstance = useIndicatorStore((s) => s.addInstance);
  const search = useIndicatorStore((s) => s.search);
  const setSearch = useIndicatorStore((s) => s.setSearch);
  const favorites = useIndicatorStore((s) => s.favorites);

  const plugins = listIndicatorPlugins().filter(
    (p) =>
      !search ||
      p.meta.label.toLowerCase().includes(search.toLowerCase()) ||
      p.meta.id.includes(search.toLowerCase()),
  );

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setMenuOpen(!menuOpen)}
        className={cn(
          "h-7 rounded-sm border px-2 text-[10px] uppercase tracking-wide",
          menuOpen
            ? "border-primary/40 bg-primary/10 text-primary"
            : "border-border text-muted hover:text-foreground",
        )}
      >
        Indicators
      </button>
      {menuOpen ? (
        <div className="absolute left-0 top-full z-40 mt-1 w-64 rounded-sm border border-border bg-panel-elevated p-2 shadow-lg">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search…"
            className="mb-2 w-full rounded-sm border border-border bg-panel px-2 py-1 text-[11px] focus:border-primary/50 focus:outline-none"
          />
          <div className="mb-2 text-[9px] uppercase tracking-wide text-muted-foreground">
            Quick panes
          </div>
          {(["rsi", "macd", "volume", "ema20", "bollinger"] as const).map((key) => (
            <label
              key={key}
              className="flex cursor-pointer items-center gap-2 rounded-sm px-1.5 py-1 text-[11px] hover:bg-panel"
            >
              <input
                type="checkbox"
                checked={!!flags[key as keyof IndicatorFlags]}
                onChange={() => toggleFlag(key as keyof IndicatorFlags)}
                className="accent-primary"
              />
              {key}
            </label>
          ))}
          <div className="my-2 border-t border-border" />
          <div className="mb-1 text-[9px] uppercase tracking-wide text-muted-foreground">
            Plugins {favorites.length ? `(★ ${favorites.length})` : ""}
          </div>
          <div className="max-h-40 overflow-y-auto">
            {plugins.map((p) => (
              <button
                key={p.meta.id}
                type="button"
                onClick={() => addInstance(p.meta.id)}
                className="flex w-full items-center justify-between rounded-sm px-1.5 py-1 text-left text-[11px] hover:bg-panel"
              >
                <span>{p.meta.label}</span>
                <span className="text-[9px] text-muted">{p.meta.category}</span>
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => {
              setPanelOpen(true);
              setMenuOpen(false);
            }}
            className="mt-2 w-full rounded-sm border border-border py-1 text-[10px] uppercase text-muted hover:text-foreground"
          >
            Open manager
          </button>
        </div>
      ) : null}
    </div>
  );
}
