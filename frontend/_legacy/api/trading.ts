import { apiFetch } from './client'
import type { Position, Recommendation } from '../types'

export async function placeOrder(
  recommendation: Recommendation,
): Promise<{ success: boolean; trade?: Position; reasons?: string[] }> {
  return apiFetch('/trade/order', {
    method: 'POST',
    body: JSON.stringify({
      symbol: recommendation.symbol,
      signal: recommendation.signal,
      confidence: recommendation.confidence,
      entry: recommendation.entry,
      stop_loss: recommendation.stop_loss,
      take_profit: recommendation.take_profit,
      risk_reward: recommendation.risk_reward,
      confluence: recommendation.confluence,
      timeframe: recommendation.timeframe,
    }),
  })
}

export async function getPositions(): Promise<Position[]> {
  return apiFetch<Position[]>('/trade/positions')
}

export async function closePosition(ticket: number): Promise<{ success: boolean }> {
  return apiFetch(`/trade/close/${ticket}`, { method: 'POST' })
}

export async function getPortfolioSummary(): Promise<{
  open_positions: number
  positions: Position[]
}> {
  return apiFetch('/portfolio/summary')
}

export async function getRiskLimits(): Promise<Record<string, unknown>> {
  return apiFetch('/risk/limits')
}
