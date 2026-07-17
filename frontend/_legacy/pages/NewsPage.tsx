import { useEffect, useState } from 'react'
import { getCalendar, getNews } from '../api/market'
import { SymbolSelector } from '../components/SymbolSelector'
import type { NewsEvent } from '../types'

export function NewsPage() {
  const [symbol, setSymbol] = useState('EURUSD')
  const [timeframe, setTimeframe] = useState('M15')
  const [news, setNews] = useState<NewsEvent[]>([])
  const [calendar, setCalendar] = useState<NewsEvent[]>([])

  useEffect(() => {
    getNews(symbol).then(setNews).catch(() => setNews([]))
    getCalendar().then(setCalendar).catch(() => setCalendar([]))
  }, [symbol])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">News & Calendar</h1>
        <SymbolSelector
          symbol={symbol}
          timeframe={timeframe}
          onSymbolChange={setSymbol}
          onTimeframeChange={setTimeframe}
        />
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Symbol Headlines</h2>
        {news.map((item) => (
          <article
            key={item.id}
            className="rounded-xl border border-slate-800 bg-slate-900/60 p-4"
          >
            <div className="mb-1 flex items-center gap-2">
              <span className="rounded bg-slate-800 px-2 py-0.5 text-xs">{item.impact}</span>
              <span className="text-xs text-slate-500">{item.published_at}</span>
            </div>
            <h3 className="font-medium">{item.title}</h3>
            {item.summary && <p className="mt-2 text-sm text-slate-400">{item.summary}</p>}
          </article>
        ))}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Economic Calendar</h2>
        {calendar.map((item) => (
          <article
            key={`cal-${item.id}`}
            className="rounded-xl border border-slate-800 bg-slate-900/40 p-4"
          >
            <p className="font-medium">{item.title}</p>
            <p className="text-sm text-slate-400">
              {item.symbols.join(', ')} · {item.impact} · {item.published_at}
            </p>
          </article>
        ))}
      </section>
    </div>
  )
}
