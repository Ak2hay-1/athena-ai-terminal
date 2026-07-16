import { useEffect, useState } from 'react'
import { getRecommendationHistory } from '../api/market'
import { SymbolSelector } from '../components/SymbolSelector'
import type { Recommendation } from '../types'

export function RecommendationsPage() {
  const [symbol, setSymbol] = useState('XAUUSD')
  const [timeframe, setTimeframe] = useState('M1')
  const [items, setItems] = useState<Recommendation[]>([])

  useEffect(() => {
    getRecommendationHistory(symbol, timeframe).then(setItems).catch(() => setItems([]))
  }, [symbol, timeframe])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Recommendations</h1>
        <SymbolSelector
          symbol={symbol}
          timeframe={timeframe}
          onSymbolChange={setSymbol}
          onTimeframeChange={setTimeframe}
        />
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-800">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-900 text-left text-slate-400">
            <tr>
              <th className="px-4 py-3">Signal</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3">Entry</th>
              <th className="px-4 py-3">SL</th>
              <th className="px-4 py-3">TP</th>
              <th className="px-4 py-3">Confluence</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={`${item.signal}-${index}`} className="border-t border-slate-800">
                <td className="px-4 py-3">{item.signal}</td>
                <td className="px-4 py-3">{item.confidence}%</td>
                <td className="px-4 py-3">{item.entry}</td>
                <td className="px-4 py-3">{item.stop_loss}</td>
                <td className="px-4 py-3">{item.take_profit}</td>
                <td className="px-4 py-3">{item.confluence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
