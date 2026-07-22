"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, ChevronDown, Settings2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AutoTradeFiltersForm } from "@/features/trading/components/auto-trade-filters-form";
import { cn } from "@/lib/utils";
import {
  DEFAULT_AUTO_TRADE,
  PREFERENCES_QUERY_KEY,
  autoTradeFromPreferences,
  getPreferences,
  updatePreferences,
  type AutoTradeFilters,
} from "@/services/preferences";
import { useAuthStore } from "@/store/auth-store";

export function AutoTradeControl() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<AutoTradeFilters>(DEFAULT_AUTO_TRADE);
  const [saveError, setSaveError] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  const prefsQuery = useQuery({
    queryKey: PREFERENCES_QUERY_KEY,
    queryFn: getPreferences,
    enabled: Boolean(user),
    staleTime: 30_000,
  });

  useEffect(() => {
    if (prefsQuery.data) {
      setDraft(autoTradeFromPreferences(prefsQuery.data));
    }
  }, [prefsQuery.data]);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const saveMutation = useMutation({
    mutationFn: updatePreferences,
    onSuccess: (data) => {
      queryClient.setQueryData(PREFERENCES_QUERY_KEY, data);
      setDraft(autoTradeFromPreferences(data));
      setSaveError(null);
    },
    onError: (error: Error) => {
      setSaveError(error.message || "Failed to save auto-trade settings.");
    },
  });

  if (!user) return null;

  const enabled = Boolean(prefsQuery.data?.auto_trade_enabled ?? draft.auto_trade_enabled);

  function toggleEnabled() {
    const next = !enabled;
    setDraft((prev) => ({ ...prev, auto_trade_enabled: next }));
    saveMutation.mutate({ auto_trade_enabled: next });
  }

  function saveFilters() {
    saveMutation.mutate({
      auto_trade_symbols: draft.auto_trade_symbols,
      auto_trade_timeframes: draft.auto_trade_timeframes,
      auto_trade_min_confidence: draft.auto_trade_min_confidence,
      auto_trade_min_confluence: draft.auto_trade_min_confluence,
      auto_trade_min_rr: draft.auto_trade_min_rr,
      auto_trade_volume: draft.auto_trade_volume,
    });
  }

  return (
    <div ref={rootRef} className="relative">
      <div className="flex items-center">
        <Button
          type="button"
          size="sm"
          variant={enabled ? "bullish" : "outline"}
          className={cn(
            "hidden gap-1.5 rounded-r-none sm:inline-flex",
            enabled && "border-r-0",
          )}
          onClick={toggleEnabled}
          disabled={saveMutation.isPending || prefsQuery.isLoading}
          aria-pressed={enabled}
          title={
            enabled
              ? "Auto Trade ON — Athena signals will place orders automatically"
              : "Auto Trade OFF"
          }
        >
          <Bot className="h-3.5 w-3.5" />
          Auto Trade {enabled ? "ON" : "OFF"}
        </Button>
        <Button
          type="button"
          size="sm"
          variant={enabled ? "bullish" : "outline"}
          className="hidden rounded-l-none border-l border-border/60 px-2 sm:inline-flex"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-label="Auto trade filters"
        >
          <Settings2 className="h-3.5 w-3.5" />
          <ChevronDown
            className={cn("h-3 w-3 transition-transform", open && "rotate-180")}
          />
        </Button>
        <Button
          type="button"
          size="icon"
          variant={enabled ? "bullish" : "ghost"}
          className="sm:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Auto trade"
        >
          <Bot className="h-4 w-4" />
        </Button>
      </div>

      {open ? (
        <div className="absolute top-full right-0 z-50 mt-2 w-[min(100vw-2rem,22rem)] rounded-sm border border-border bg-background p-3 shadow-lg">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div>
              <p className="text-sm font-medium">Auto Trade</p>
              <p className="text-[11px] text-muted-foreground">
                Places MT5 orders when Athena signals match your filters
              </p>
            </div>
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                className="accent-primary"
                checked={enabled}
                onChange={toggleEnabled}
                disabled={saveMutation.isPending}
              />
              Enabled
            </label>
          </div>

          <AutoTradeFiltersForm
            value={draft}
            onChange={setDraft}
            compact
          />

          {saveError ? (
            <p className="mt-2 text-xs text-bearish">{saveError}</p>
          ) : null}

          <div className="mt-3 flex justify-end gap-2">
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setOpen(false)}
            >
              Close
            </Button>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={saveFilters}
              disabled={saveMutation.isPending}
            >
              {saveMutation.isPending ? "Saving…" : "Save filters"}
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
