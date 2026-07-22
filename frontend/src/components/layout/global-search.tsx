"use client";

import { useEffect, useMemo, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { adminNav, primaryNav } from "@/constants/navigation";
import { MARKET_SYMBOLS } from "@/constants/markets";
import { cn } from "@/lib/utils";
import { listJournal } from "@/services/journal";
import { getRecommendationHistory } from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";
import { useUiStore } from "@/store/ui-store";

type SearchHit = {
  id: string;
  group: "Pages" | "Markets" | "Recommendations" | "Journal";
  label: string;
  detail?: string;
  href: string;
};

function matches(query: string, ...parts: Array<string | null | undefined>) {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return parts.some((part) => part?.toLowerCase().includes(q));
}

export function GlobalSearch() {
  const open = useUiStore((s) => s.searchOpen);
  const setSearchOpen = useUiStore((s) => s.setSearchOpen);
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "ADMIN";
  const timeframe = useDashboardStore((s) => s.timeframe);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const deep = query.trim().length >= 2;

  const recsQuery = useQuery({
    queryKey: ["search", "recommendations", timeframe],
    queryFn: () => getRecommendationHistory(null, timeframe, 20),
    enabled: open && deep && Boolean(user),
    staleTime: 30_000,
  });

  const journalQuery = useQuery({
    queryKey: ["search", "journal"],
    queryFn: () => listJournal({ limit: 30 }),
    enabled: open && deep && Boolean(user),
    staleTime: 30_000,
  });

  const hits = useMemo(() => {
    const results: SearchHit[] = [];
    const navItems = [
      ...primaryNav,
      ...(isAdmin ? adminNav : []),
    ];

    for (const item of navItems) {
      if (matches(query, item.label, item.href)) {
        results.push({
          id: `page-${item.href}`,
          group: "Pages",
          label: item.label,
          detail: item.href,
          href: item.href,
        });
      }
    }

    for (const symbol of MARKET_SYMBOLS) {
      if (matches(query, symbol)) {
        results.push({
          id: `mkt-${symbol}`,
          group: "Markets",
          label: symbol,
          detail: "Market detail",
          href: `/markets/${symbol.toLowerCase()}`,
        });
      }
    }

    if (deep) {
      for (const rec of recsQuery.data ?? []) {
        if (matches(query, rec.symbol, rec.signal, String(rec.id))) {
          results.push({
            id: `rec-${rec.id}`,
            group: "Recommendations",
            label: `${rec.symbol} ${rec.signal}`,
            detail: `${rec.timeframe} · ${rec.confidence}%`,
            href: `/recommendations/${rec.id}`,
          });
        }
      }
      for (const entry of journalQuery.data ?? []) {
        if (matches(query, entry.title, entry.body, entry.symbol)) {
          results.push({
            id: `journal-${entry.id}`,
            group: "Journal",
            label: entry.title,
            detail: entry.entryType,
            href: entry.recommendationId
              ? `/recommendations/${entry.recommendationId}`
              : "/journal",
          });
        }
      }
    }

    return results.slice(0, 40);
  }, [deep, isAdmin, journalQuery.data, query, recsQuery.data]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query, hits.length]);

  useEffect(() => {
    if (!open) {
      setQuery("");
      return;
    }
    const timer = window.setTimeout(() => inputRef.current?.focus(), 10);
    return () => window.clearTimeout(timer);
  }, [open]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const isPalette =
        (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";
      if (isPalette) {
        event.preventDefault();
        setSearchOpen(true);
        return;
      }
      if (!open) return;
      if (event.key === "Escape") {
        event.preventDefault();
        setSearchOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, setSearchOpen]);

  if (!open) return null;

  function go(href: string) {
    setSearchOpen(false);
    router.push(href);
  }

  function onKeyDown(event: ReactKeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, Math.max(hits.length - 1, 0)));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (event.key === "Enter" && hits[activeIndex]) {
      event.preventDefault();
      go(hits[activeIndex].href);
    }
  }

  const groups = ["Pages", "Markets", "Recommendations", "Journal"] as const;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 px-4 pt-[12vh]">
      <button
        type="button"
        className="absolute inset-0"
        aria-label="Close search"
        onClick={() => setSearchOpen(false)}
      />
      <div className="relative w-full max-w-xl overflow-hidden rounded-sm border border-border bg-sidebar shadow-xl">
        <div className="flex items-center gap-2 border-b border-border px-3">
          <Search className="h-4 w-4 text-muted-foreground" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Search markets, pages, recommendations, journal…"
            className="h-11 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          <kbd className="hidden rounded-sm border border-border px-1.5 py-0.5 text-[10px] text-muted sm:inline">
            Esc
          </kbd>
        </div>
        <div className="max-h-[50vh] overflow-y-auto p-2">
          {hits.length === 0 ? (
            <p className="px-2 py-8 text-center text-sm text-muted">
              {deep
                ? "No matches"
                : "Type to filter pages and markets · 2+ chars for recs & journal"}
            </p>
          ) : (
            groups.map((group) => {
              const items = hits.filter((h) => h.group === group);
              if (items.length === 0) return null;
              return (
                <div key={group} className="mb-2">
                  <p className="px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                    {group}
                  </p>
                  {items.map((hit) => {
                    const globalIndex = hits.findIndex((h) => h.id === hit.id);
                    return (
                      <button
                        key={hit.id}
                        type="button"
                        className={cn(
                          "flex w-full items-center justify-between gap-3 rounded-sm px-2 py-2 text-left text-sm",
                          globalIndex === activeIndex
                            ? "bg-primary/15 text-foreground"
                            : "hover:bg-panel-elevated",
                        )}
                        onMouseEnter={() => setActiveIndex(globalIndex)}
                        onClick={() => go(hit.href)}
                      >
                        <span className="truncate font-medium">{hit.label}</span>
                        {hit.detail ? (
                          <span className="shrink-0 text-[11px] text-muted">
                            {hit.detail}
                          </span>
                        ) : null}
                      </button>
                    );
                  })}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
