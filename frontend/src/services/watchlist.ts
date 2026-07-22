import { apiFetch } from "@/services/api-client";

export type WatchlistEntry = {
  id: number;
  symbol: string;
  timeframe: string;
  enabled: boolean;
};

export async function listWatchlist(): Promise<WatchlistEntry[]> {
  return apiFetch<WatchlistEntry[]>("/watchlist");
}

export async function addWatchlistEntry(input: {
  symbol: string;
  timeframe: string;
  enabled?: boolean;
}): Promise<WatchlistEntry> {
  return apiFetch<WatchlistEntry>("/watchlist", {
    method: "POST",
    body: JSON.stringify({
      symbol: input.symbol,
      timeframe: input.timeframe,
      enabled: input.enabled ?? true,
    }),
  });
}

export async function removeWatchlistEntry(entryId: number): Promise<void> {
  await apiFetch<void>(`/watchlist/${entryId}`, {
    method: "DELETE",
  });
}
