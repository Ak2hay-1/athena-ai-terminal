"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MARKET_SYMBOLS } from "@/constants/markets";
import { relativeTime } from "@/lib/mappers";
import { cn, formatPercent } from "@/lib/utils";
import {
  createJournalEntry,
  deleteJournalEntry,
  listJournal,
  updateJournalEntry,
  type JournalEntry,
  type JournalEntryType,
} from "@/services/journal";
import { getRecommendationHistory } from "@/services/recommendations";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";

const ENTRY_TYPES: Array<JournalEntryType | "ALL"> = [
  "ALL",
  "note",
  "trade_review",
  "recommendation_review",
  "auto_close",
];

function entryHref(entry: JournalEntry): string | null {
  if (entry.recommendationId) return `/recommendations/${entry.recommendationId}`;
  if (entry.symbol) return `/markets/${entry.symbol.toLowerCase()}`;
  return null;
}

export function JournalView() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const storeSymbol = useDashboardStore((s) => s.symbol);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setSymbol = useDashboardStore((s) => s.setSymbol);

  const [symbolFilter, setSymbolFilter] = useState(storeSymbol);
  const [typeFilter, setTypeFilter] = useState<JournalEntryType | "ALL">("ALL");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editBody, setEditBody] = useState("");

  const isAll = symbolFilter === "ALL";
  const historySymbol = isAll ? null : symbolFilter;

  const journalQuery = useQuery({
    queryKey: ["journal", symbolFilter, typeFilter],
    queryFn: () =>
      listJournal({
        symbol: isAll ? null : symbolFilter,
        entryType: typeFilter === "ALL" ? null : typeFilter,
        limit: 100,
      }),
    enabled: Boolean(user),
    refetchInterval: 30_000,
  });

  const historyQuery = useQuery({
    queryKey: ["recommendation", "history", symbolFilter, timeframe, 10],
    queryFn: () => getRecommendationHistory(historySymbol, timeframe, 10),
    enabled: Boolean(user),
    refetchInterval: 60_000,
  });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["journal"] });
  };

  const createMutation = useMutation({
    mutationFn: createJournalEntry,
    onSuccess: () => {
      setTitle("");
      setBody("");
      invalidate();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, ...input }: { id: number; title: string; body: string }) =>
      updateJournalEntry(id, input),
    onSuccess: () => {
      setEditingId(null);
      invalidate();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteJournalEntry,
    onSuccess: invalidate,
  });

  const pinRecMutation = useMutation({
    mutationFn: (rec: {
      id: number;
      symbol: string;
      signal: string;
      confidence: number;
      reasons: string[];
    }) =>
      createJournalEntry({
        entryType: "recommendation_review",
        title: `${rec.symbol} ${rec.signal} review`,
        body:
          rec.reasons.slice(0, 3).join(" · ") ||
          `Confidence ${formatPercent(rec.confidence)}`,
        symbol: rec.symbol,
        recommendationId: rec.id,
        tags: ["pinned"],
      }),
    onSuccess: invalidate,
  });

  const entries = journalQuery.data ?? [];

  return (
    <div className="mx-auto max-w-[1100px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Journal
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Trading journal</h1>
          <p className="mt-1 text-sm text-muted">
            Persisted notes, trade reviews, and recommendation reviews
            {isAll ? " · all pairs" : ` · ${symbolFilter}`}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={symbolFilter}
            onChange={(event) => {
              const next = event.target.value;
              setSymbolFilter(next);
              if (next !== "ALL") setSymbol(next);
            }}
            className="h-9 rounded-sm border border-border bg-panel px-3 font-mono text-sm outline-none focus:border-primary/50"
          >
            <option value="ALL">ALL</option>
            {MARKET_SYMBOLS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select
            value={typeFilter}
            onChange={(event) =>
              setTypeFilter(event.target.value as JournalEntryType | "ALL")
            }
            className="h-9 rounded-sm border border-border bg-panel px-3 text-sm outline-none focus:border-primary/50"
          >
            {ENTRY_TYPES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Card>
          <CardContent className="pt-5">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
              Journal entries
            </p>
            <p className="mt-1 font-mono text-2xl">{entries.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
              Suggest pin
            </p>
            <p className="mt-1 font-mono text-2xl">
              {historyQuery.data?.length ?? 0}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New note</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title"
            className="h-9 w-full rounded-sm border border-border bg-panel px-3 text-sm outline-none focus:border-primary/50"
          />
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Notes, lessons, setup context…"
            rows={3}
            className="w-full rounded-sm border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-primary/50"
          />
          <Button
            disabled={!title.trim() || createMutation.isPending}
            onClick={() =>
              createMutation.mutate({
                entryType: "note",
                title: title.trim(),
                body: body.trim(),
                symbol: isAll ? null : symbolFilter,
              })
            }
          >
            Save note
          </Button>
        </CardContent>
      </Card>

      {(historyQuery.data?.length ?? 0) > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Suggest pin</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {(historyQuery.data ?? []).slice(0, 6).map((rec) => (
              <Button
                key={`rec-${rec.id}`}
                size="sm"
                variant="secondary"
                disabled={pinRecMutation.isPending}
                onClick={() =>
                  pinRecMutation.mutate({
                    id: Number(rec.id),
                    symbol: rec.symbol,
                    signal: rec.signal,
                    confidence: rec.confidence,
                    reasons: rec.reasons,
                  })
                }
              >
                Pin {rec.symbol} {rec.signal}
              </Button>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Timeline</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {journalQuery.isLoading ? (
            <p className="py-8 text-center text-sm text-muted">Loading journal…</p>
          ) : entries.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted">
              Journal is empty — add a note or pin a recommendation.
            </p>
          ) : (
            entries.map((entry) => {
              const href = entryHref(entry);
              const isEditing = editingId === entry.id;
              return (
                <div
                  key={entry.id}
                  className="rounded-sm border border-border/70 bg-background/30 px-3 py-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge tone="ai">{entry.entryType}</Badge>
                      {entry.symbol ? (
                        <Badge tone="primary">{entry.symbol}</Badge>
                      ) : null}
                      {href ? (
                        <Link
                          href={href}
                          className="text-sm font-medium hover:text-primary"
                        >
                          {entry.title}
                        </Link>
                      ) : (
                        <p className="text-sm font-medium">{entry.title}</p>
                      )}
                    </div>
                    <span className="text-[11px] text-muted">
                      {entry.createdAt ? relativeTime(entry.createdAt) : "—"}
                    </span>
                  </div>

                  {isEditing ? (
                    <div className="mt-3 space-y-2">
                      <input
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        className="h-8 w-full rounded-sm border border-border bg-panel px-2 text-sm outline-none"
                      />
                      <textarea
                        value={editBody}
                        onChange={(e) => setEditBody(e.target.value)}
                        rows={3}
                        className="w-full rounded-sm border border-border bg-panel px-2 py-1.5 text-sm outline-none"
                      />
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          disabled={updateMutation.isPending || !editTitle.trim()}
                          onClick={() =>
                            updateMutation.mutate({
                              id: entry.id,
                              title: editTitle.trim(),
                              body: editBody,
                            })
                          }
                        >
                          Save
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => setEditingId(null)}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className={cn("mt-2 text-sm text-zinc-300")}>{entry.body}</p>
                      {entry.tags.length > 0 ? (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {entry.tags.map((tag) => (
                            <span
                              key={tag}
                              className="rounded-sm bg-panel px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      ) : null}
                      <div className="mt-3 flex gap-2">
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => {
                            setEditingId(entry.id);
                            setEditTitle(entry.title);
                            setEditBody(entry.body);
                          }}
                        >
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={deleteMutation.isPending}
                          onClick={() => deleteMutation.mutate(entry.id)}
                        >
                          Delete
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              );
            })
          )}
        </CardContent>
      </Card>
    </div>
  );
}
