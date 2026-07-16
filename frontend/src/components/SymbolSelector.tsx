import { SYMBOLS, TIMEFRAMES } from '../config'

interface Props {
  symbol: string
  timeframe: string
  onSymbolChange: (symbol: string) => void
  onTimeframeChange: (timeframe: string) => void
}

export function SymbolSelector({
  symbol,
  timeframe,
  onSymbolChange,
  onTimeframeChange,
}: Props) {
  return (
    <div className="flex flex-wrap gap-3">
      <label className="flex flex-col gap-1 text-sm text-slate-400">
        Symbol
        <select
          className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
          value={symbol}
          onChange={(event) => onSymbolChange(event.target.value)}
        >
          {SYMBOLS.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm text-slate-400">
        Timeframe
        <select
          className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
          value={timeframe}
          onChange={(event) => onTimeframeChange(event.target.value)}
        >
          {TIMEFRAMES.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
