import { apiFetch } from "@/services/api-client";

export type JournalEntryType =
  | "note"
  | "trade_review"
  | "recommendation_review"
  | "auto_close";

export type JournalEntry = {
  id: number;
  entryType: JournalEntryType;
  title: string;
  body: string;
  symbol: string | null;
  tags: string[];
  recommendationId: number | null;
  paperPositionId: number | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type JournalCreateInput = {
  entryType?: JournalEntryType;
  title: string;
  body?: string;
  symbol?: string | null;
  tags?: string[];
  recommendationId?: number | null;
  paperPositionId?: number | null;
};

export type JournalUpdateInput = {
  title?: string;
  body?: string;
  tags?: string[];
  symbol?: string | null;
  entryType?: JournalEntryType;
};

type JournalRaw = {
  id: number;
  entry_type: string;
  title: string;
  body: string;
  symbol: string | null;
  tags: string[] | null;
  recommendation_id: number | null;
  paper_position_id: number | null;
  created_at: string | null;
  updated_at: string | null;
};

function mapEntry(raw: JournalRaw): JournalEntry {
  return {
    id: raw.id,
    entryType: (raw.entry_type || "note") as JournalEntryType,
    title: raw.title,
    body: raw.body || "",
    symbol: raw.symbol,
    tags: Array.isArray(raw.tags) ? raw.tags : [],
    recommendationId: raw.recommendation_id,
    paperPositionId: raw.paper_position_id,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
  };
}

export async function listJournal(params?: {
  symbol?: string | null;
  entryType?: JournalEntryType | null;
  limit?: number;
}): Promise<JournalEntry[]> {
  const search = new URLSearchParams();
  if (params?.symbol) search.set("symbol", params.symbol);
  if (params?.entryType) search.set("entry_type", params.entryType);
  if (params?.limit) search.set("limit", String(params.limit));
  const qs = search.toString();
  const raw = await apiFetch<JournalRaw[]>(`/journal${qs ? `?${qs}` : ""}`);
  return raw.map(mapEntry);
}

export async function createJournalEntry(
  input: JournalCreateInput,
): Promise<JournalEntry> {
  const raw = await apiFetch<JournalRaw>("/journal", {
    method: "POST",
    body: JSON.stringify({
      entry_type: input.entryType ?? "note",
      title: input.title,
      body: input.body ?? "",
      symbol: input.symbol ?? null,
      tags: input.tags ?? [],
      recommendation_id: input.recommendationId ?? null,
      paper_position_id: input.paperPositionId ?? null,
    }),
  });
  return mapEntry(raw);
}

export async function updateJournalEntry(
  id: number,
  input: JournalUpdateInput,
): Promise<JournalEntry> {
  const body: Record<string, unknown> = {};
  if (input.title !== undefined) body.title = input.title;
  if (input.body !== undefined) body.body = input.body;
  if (input.tags !== undefined) body.tags = input.tags;
  if (input.symbol !== undefined) body.symbol = input.symbol;
  if (input.entryType !== undefined) body.entry_type = input.entryType;
  const raw = await apiFetch<JournalRaw>(`/journal/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  return mapEntry(raw);
}

export async function deleteJournalEntry(id: number): Promise<void> {
  await apiFetch<void>(`/journal/${id}`, { method: "DELETE" });
}
