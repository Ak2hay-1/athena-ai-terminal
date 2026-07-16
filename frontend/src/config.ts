export const API_URL =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export const WS_URL =
  import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws'

export const SYMBOLS = [
  'XAUUSD',
  'EURUSD',
  'GBPUSD',
  'USDJPY',
  'AUDUSD',
  'USDCAD',
  'NZDUSD',
  'USDCHF',
]

export const TIMEFRAMES = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
