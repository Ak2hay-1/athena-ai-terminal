import type { Candle } from "@/types";
import type { Candlestick } from "../types";

/** Map app Candle ↔ module Candlestick (identical shape today). */
export function candleToCandlestick(c: Candle): Candlestick {
  return c;
}

export function candlestickToCandle(c: Candlestick): Candle {
  return c;
}

export function candlesToCandlesticks(candles: Candle[]): Candlestick[] {
  return candles;
}
