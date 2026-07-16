import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  analyzeMarket,
  getLatestRecommendation,
  getNewsContext,
} from '../api/market'
import { getHealth } from '../api/client'
import { SymbolSelector } from '../components/SymbolSelector'
import { useMarketWebSocket } from '../hooks/useMarketWebSocket'
import type { NewsContext, Recommendation } from '../types'

export function DashboardPage() {
  const [symbol, setSymbol] = useState('XAUUSD')
  const [timeframe, setTimeframe] = useState('M1')
  const [health, setHealth] = useState<Record<string, string>>({})
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [news, setNews] = useState<NewsContext | null>(null)
  const [liveMessage, setLiveMessage] = useState('')

  const load = useCallback(async () => {
    setHealth(await getHealth())
    setRecommendation(await getLatestRecommendation(symbol, timeframe))
    setNews(await getNewsContext(symbol))
  }, [symbol, timeframe])

  useEffect(() => {
    load()
  }, [load])

  const onMessage = useCallback(
    (payload: Record<string, unknown>) => {
      if (payload.type === 'candle_update') {
        setLiveMessage(
          `Live update: ${payload.inserted} candles for ${payload.symbol} ${payload.timeframe}`,
        )

        if (payload.recommendation) {
          setRecommendation(payload.recommendation as Recommendation)
        }
      }
    },
    [],
  )

  const { connected } = useMarketWebSocket(symbol, timeframe, onMessage)

  const runAnalysis = async () => {
    const result = await analyzeMarket(symbol, timeframe)

    if (result.recommendation) {
      setRecommendation(result.recommendation)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-slate-400">Multi-pair AI trading intelligence</p>
        </div>
        <SymbolSelector
          symbol={symbol}
          timeframe={timeframe}
          onSymbolChange={setSymbol}
          onTimeframeChange={setTimeframe}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <p className="text-sm text-slate-400">System</p>
          <p className="text-lg font-medium capitalize">{health.status ?? 'unknown'}</p>
          <p className="text-sm text-slate-500">DB: {health.database ?? 'n/a'}</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <p className="text-sm text-slate-400">WebSocket</p>
          <p className="text-lg font-medium">{connected ? 'Connected' : 'Disconnected'}</p>
          <p className="text-sm text-slate-500">{liveMessage || 'Waiting for updates'}</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <p className="text-sm text-slate-400">News Sentiment</p>
          <p className="text-lg font-medium">{news?.sentiment ?? 'NEUTRAL'}</p>
          {news?.high_impact_upcoming && (
            <p className="text-sm text-amber-400">High-impact event approaching</p>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-medium">Latest Recommendation</h2>
          <button
            onClick={runAnalysis}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm hover:bg-emerald-500"
          >
            Run Analysis
          </button>
        </div>

        {recommendation ? (
          <div className="grid gap-3 md:grid-cols-2">
            <p>
              Signal: <span className="font-semibold text-emerald-400">{recommendation.signal}</span>
            </p>
            <p>Confidence: {recommendation.confidence}%</p>
            <p>Entry: {recommendation.entry}</p>
            <p>Stop Loss: {recommendation.stop_loss}</p>
            <p>Take Profit: {recommendation.take_profit}</p>
            <p>Confluence: {recommendation.confluence}</p>
            <ul className="md:col-span-2 list-disc pl-5 text-sm text-slate-300">
              {(recommendation.reason ?? []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="text-slate-400">No recommendation available yet.</p>
        )}
      </div>

      <div className="flex gap-3 text-sm">
        <Link className="text-emerald-400" to="/market">Open chart</Link>
        <Link className="text-emerald-400" to="/news">View news</Link>
        <Link className="text-emerald-400" to="/trading">Paper trading</Link>
      </div>
    </div>
  )
}
