import { apiFetch } from './client'
import type {
  Candle,
  NewsContext,
  NewsEvent,
  Recommendation,
} from '../types'

export async function getLatestRecommendation(
  symbol: string,
  timeframe: string,
): Promise<Recommendation | null> {
  try {
    return await apiFetch<Recommendation>(
      `/recommendations/latest?symbol=${symbol}&timeframe=${timeframe}`,
    )
  } catch {
    return null
  }
}

export async function getRecommendationHistory(
  symbol: string,
  timeframe: string,
): Promise<Recommendation[]> {
  return apiFetch<Recommendation[]>(
    `/recommendations/history?symbol=${symbol}&timeframe=${timeframe}&limit=50`,
  )
}

export async function getCandles(
  symbol: string,
  timeframe: string,
  limit = 200,
): Promise<Candle[]> {
  return apiFetch<Candle[]>(
    `/market/candles?symbol=${symbol}&timeframe=${timeframe}&limit=${limit}`,
  )
}

export async function analyzeMarket(
  symbol: string,
  timeframe: string,
): Promise<{ success: boolean; recommendation?: Recommendation }> {
  return apiFetch(
    `/ai/analyze?symbol=${symbol}&timeframe=${timeframe}`,
    { method: 'POST' },
  )
}

export async function getNews(symbol: string): Promise<NewsEvent[]> {
  return apiFetch<NewsEvent[]>(`/news/latest?symbol=${symbol}`)
}

export async function getNewsContext(symbol: string): Promise<NewsContext> {
  return apiFetch<NewsContext>(`/news/context?symbol=${symbol}`)
}

export async function getCalendar(): Promise<NewsEvent[]> {
  return apiFetch<NewsEvent[]>('/news/calendar')
}

export async function getLearningStats(
  symbol: string,
  timeframe: string,
): Promise<Record<string, unknown>> {
  return apiFetch(
    `/learning/stats?symbol=${symbol}&timeframe=${timeframe}`,
  )
}
