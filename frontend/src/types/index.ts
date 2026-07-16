export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: string
}

export interface Recommendation {
  signal: string
  confidence: number
  entry?: number
  stop_loss?: number
  take_profit?: number
  risk_reward?: number
  reason?: string[]
  trend?: string
  confluence?: number
  symbol?: string
  timeframe?: string
}

export interface Candle {
  symbol: string
  timeframe: string
  time: string
  open: number
  high: number
  low: number
  close: number
  tick_volume: number
}

export interface NewsEvent {
  id: number
  title: string
  summary?: string
  impact: string
  sentiment_score: number
  published_at: string
  symbols: string[]
}

export interface NewsContext {
  sentiment: string
  score: number
  high_impact_upcoming: boolean
  headlines: string[]
  upcoming_events: Array<{
    title: string
    impact: string
    published_at: string
  }>
}

export interface Position {
  ticket: number
  symbol: string
  signal: string
  entry: number
  stop_loss: number
  take_profit: number
  volume: number
  status: string
}
