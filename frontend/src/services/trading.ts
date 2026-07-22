import { apiFetch } from "@/services/api-client";
import { toNumber } from "@/lib/mappers";
import type { Position, Recommendation } from "@/types";

interface PositionRaw {
  ticket: number;
  symbol: string;
  signal: string;
  entry: number;
  stop_loss: number;
  take_profit: number;
  volume: number;
  status: string;
  order_type?: string;
  pnl?: number;
  mark?: number;
  opened_at?: string;
}

export interface OrderResponse {
  success: boolean;
  reasons?: string[];
  trade?: PositionRaw;
  validation?: string[];
}

export type PlaceOrderInput = {
  symbol: string;
  signal: string;
  confidence: number;
  entry: number;
  stopLoss: number;
  takeProfit: number;
  riskReward: number;
  confluence?: number;
  timeframe: string;
  volume?: number;
};

function mapPosition(item: PositionRaw): Position {
  return {
    id: String(item.ticket),
    symbol: String(item.symbol).toUpperCase(),
    side: String(item.signal).toUpperCase().includes("SELL") ? "SELL" : "BUY",
    entry: toNumber(item.entry),
    stopLoss: toNumber(item.stop_loss),
    takeProfit: toNumber(item.take_profit),
    volume: toNumber(item.volume, 1),
    pnl: toNumber(item.pnl),
    status: String(item.status).toUpperCase() === "CLOSED" ? "closed" : "open",
  };
}

export async function getPositions(): Promise<Position[]> {
  try {
    const raw = await apiFetch<PositionRaw[]>("/trade/positions");
    return raw.map(mapPosition);
  } catch (error) {
    console.warn("Failed to load positions", error);
    return [];
  }
}

export async function placeOrder(
  input: PlaceOrderInput,
): Promise<OrderResponse> {
  return apiFetch<OrderResponse>("/trade/order", {
    method: "POST",
    body: JSON.stringify({
      symbol: input.symbol,
      signal: input.signal,
      confidence: input.confidence,
      entry: input.entry,
      stop_loss: input.stopLoss,
      take_profit: input.takeProfit,
      risk_reward: input.riskReward,
      confluence: input.confluence,
      timeframe: input.timeframe,
      volume: input.volume ?? 0.01,
    }),
  });
}

export async function placeOrderFromRecommendation(
  recommendation: Recommendation,
  volume = 0.01,
): Promise<OrderResponse> {
  const signal = recommendation.signal.includes("SELL")
    ? "SELL"
    : recommendation.signal.includes("BUY")
      ? "BUY"
      : recommendation.signal;

  return placeOrder({
    symbol: recommendation.symbol,
    signal,
    confidence: recommendation.confidence,
    entry: recommendation.entry,
    stopLoss: recommendation.stopLoss,
    takeProfit: recommendation.takeProfit,
    riskReward: recommendation.riskReward,
    confluence: recommendation.confluence,
    timeframe: recommendation.timeframe,
    volume,
  });
}

export async function closePosition(
  ticket: string | number,
): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/trade/close/${ticket}`, {
    method: "POST",
  });
}
