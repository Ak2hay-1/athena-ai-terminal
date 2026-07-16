import { useEffect, useState } from 'react'
import {
  closePosition,
  getPortfolioSummary,
  getPositions,
  placeOrder,
} from '../api/trading'
import { getLatestRecommendation } from '../api/market'
import { SymbolSelector } from '../components/SymbolSelector'
import type { Position, Recommendation } from '../types'

export function TradingPage() {
  const [symbol, setSymbol] = useState('XAUUSD')
  const [timeframe, setTimeframe] = useState('M1')
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [message, setMessage] = useState('')

  const refresh = async () => {
    setRecommendation(await getLatestRecommendation(symbol, timeframe))
    setPositions(await getPositions())
    await getPortfolioSummary()
  }

  useEffect(() => {
    refresh()
  }, [symbol, timeframe])

  const execute = async () => {
    if (!recommendation) {
      return
    }

    const result = await placeOrder({
      ...recommendation,
      symbol,
      timeframe,
    })

    setMessage(
      result.success
        ? `Order placed: ticket ${result.trade?.ticket}`
        : (result.reasons ?? ['Order rejected']).join(', '),
    )

    await refresh()
  }

  const close = async (ticket: number) => {
    await closePosition(ticket)
    await refresh()
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Paper Trading</h1>
          <p className="text-sm text-slate-400">Execution mode: Paper</p>
        </div>
        <SymbolSelector
          symbol={symbol}
          timeframe={timeframe}
          onSymbolChange={setSymbol}
          onTimeframeChange={setTimeframe}
        />
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="mb-4 text-lg font-medium">Place Order from Recommendation</h2>
        {recommendation ? (
          <div className="space-y-3">
            <p>
              {recommendation.signal} · {recommendation.confidence}% · Entry {recommendation.entry}
            </p>
            <button
              onClick={execute}
              className="rounded-lg bg-emerald-600 px-4 py-2 hover:bg-emerald-500"
            >
              Execute Paper Trade
            </button>
          </div>
        ) : (
          <p className="text-slate-400">No recommendation loaded.</p>
        )}
        {message && <p className="mt-3 text-sm text-slate-300">{message}</p>}
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="mb-4 text-lg font-medium">Open Positions</h2>
        {positions.length === 0 ? (
          <p className="text-slate-400">No open positions.</p>
        ) : (
          <div className="space-y-3">
            {positions.map((position) => (
              <div
                key={position.ticket}
                className="flex items-center justify-between rounded-lg border border-slate-800 px-4 py-3"
              >
                <div>
                  <p className="font-medium">
                    #{position.ticket} {position.symbol} {position.signal}
                  </p>
                  <p className="text-sm text-slate-400">
                    Entry {position.entry} · SL {position.stop_loss} · TP {position.take_profit}
                  </p>
                </div>
                <button
                  onClick={() => close(position.ticket)}
                  className="rounded-lg border border-slate-700 px-3 py-1 text-sm"
                >
                  Close
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
