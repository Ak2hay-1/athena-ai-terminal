import { useEffect, useState } from 'react'
import { getCandles } from '../api/market'
import { PriceChart } from '../components/PriceChart'
import { SymbolSelector } from '../components/SymbolSelector'
import type { Candle } from '../types'

export function MarketPage() {
  const [symbol, setSymbol] = useState('EURUSD')
  const [timeframe, setTimeframe] = useState('M15')
  const [candles, setCandles] = useState<Candle[]>([])

  useEffect(() => {
    getCandles(symbol, timeframe, 300).then(setCandles).catch(() => setCandles([]))
  }, [symbol, timeframe])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Market</h1>
        <SymbolSelector
          symbol={symbol}
          timeframe={timeframe}
          onSymbolChange={setSymbol}
          onTimeframeChange={setTimeframe}
        />
      </div>

      {candles.length > 0 ? (
        <PriceChart candles={candles} />
      ) : (
        <p className="text-slate-400">No candle data available for this pair.</p>
      )}
    </div>
  )
}
