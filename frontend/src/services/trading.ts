import { apiFetch } from "@/services/api-client";
import { toNumber } from "@/lib/mappers";
import type { Position } from "@/types";

interface PositionRaw {
  ticket: number;
  symbol: string;
  signal: string;
  entry: number;
  stop_loss: number;
  take_profit: number;
  volume: number;
  status: string;
  pnl?: number;
}

export async function getPositions(): Promise<Position[]> {
  try {
    const raw = await apiFetch<PositionRaw[]>("/trade/positions");
    return raw.map((item) => ({
      id: String(item.ticket),
      symbol: String(item.symbol).toUpperCase(),
      side: String(item.signal).toUpperCase().includes("SELL") ? "SELL" : "BUY",
      entry: toNumber(item.entry),
      stopLoss: toNumber(item.stop_loss),
      takeProfit: toNumber(item.take_profit),
      volume: toNumber(item.volume, 1),
      pnl: toNumber(item.pnl),
      status: String(item.status).toUpperCase() === "CLOSED" ? "closed" : "open",
    }));
  } catch {
    return [];
  }
}
