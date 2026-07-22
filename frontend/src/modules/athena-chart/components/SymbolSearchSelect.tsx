"use client";

import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";
import { MARKET_SYMBOLS } from "@/constants/markets";
import { cn } from "@/lib/utils";

interface SymbolSearchSelectProps {
  value: string;
  onChange: (symbol: string) => void;
  symbols?: readonly string[];
  className?: string;
  buttonClassName?: string;
  "aria-label"?: string;
}

export function SymbolSearchSelect({
  value,
  onChange,
  symbols = MARKET_SYMBOLS,
  className,
  buttonClassName,
  "aria-label": ariaLabel = "Pair",
}: SymbolSearchSelectProps) {
  const listId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlight, setHighlight] = useState(0);

  const filtered = useMemo(() => {
    const q = query.trim().toUpperCase();
    if (!q) return [...symbols];
    return symbols.filter((s) => s.includes(q));
  }, [query, symbols]);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setHighlight(0);
    const t = window.setTimeout(() => inputRef.current?.focus(), 0);
    return () => window.clearTimeout(t);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  useEffect(() => {
    setHighlight((h) =>
      filtered.length === 0 ? 0 : Math.min(h, filtered.length - 1),
    );
  }, [filtered.length]);

  const select = useCallback(
    (symbol: string) => {
      onChange(symbol.toUpperCase());
      setOpen(false);
    },
    [onChange],
  );

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, Math.max(0, filtered.length - 1)));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      const pick = filtered[highlight];
      if (pick) select(pick);
    }
  };

  return (
    <div ref={rootRef} className={cn("relative", className)}>
      <button
        type="button"
        aria-label={ariaLabel}
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={listId}
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "flex h-7 min-w-[96px] items-center justify-between gap-1.5 rounded-sm border border-border bg-panel px-1.5 font-mono text-[11px] text-foreground focus:border-primary/50 focus:outline-none",
          buttonClassName,
        )}
      >
        <span>{value}</span>
        <span className="text-muted" aria-hidden>
          ▾
        </span>
      </button>
      {open ? (
        <div
          className="absolute left-0 top-full z-50 mt-1 w-44 overflow-hidden rounded-sm border border-border bg-panel shadow-lg"
          onKeyDown={onKeyDown}
        >
          <input
            ref={inputRef}
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search pair…"
            aria-label="Search pair"
            className="h-8 w-full border-b border-border bg-transparent px-2 font-mono text-[11px] text-foreground outline-none placeholder:text-muted"
          />
          <ul
            id={listId}
            role="listbox"
            aria-label="Pairs"
            className="max-h-56 overflow-y-auto py-0.5"
          >
            {filtered.length === 0 ? (
              <li className="px-2 py-1.5 font-mono text-[10px] text-muted">
                No matches
              </li>
            ) : (
              filtered.map((s, i) => (
                <li key={s} role="option" aria-selected={s === value}>
                  <button
                    type="button"
                    onClick={() => select(s)}
                    onMouseEnter={() => setHighlight(i)}
                    className={cn(
                      "flex w-full px-2 py-1 font-mono text-[11px] text-left",
                      i === highlight || s === value
                        ? "bg-primary/15 text-primary"
                        : "text-foreground hover:bg-white/5",
                    )}
                  >
                    {s}
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
