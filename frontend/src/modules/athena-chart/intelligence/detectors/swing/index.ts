import type { Candlestick } from "../../../types";
import type { IntelligenceSettings, SwingPoint } from "../../types";
import { atrApprox, makeId, scoreOf, trace } from "../../utils/scoring";

/**
 * Configurable fractal swing detector.
 * Supports swing length, sensitivity, noise filter, adaptive mode.
 */
export function detectSwings(
  candles: Candlestick[],
  settings: IntelligenceSettings,
): SwingPoint[] {
  if (candles.length < settings.swingLength * 2 + 1) return [];

  let len = Math.max(2, Math.floor(settings.swingLength));
  if (settings.adaptiveMode) {
    const atr = atrApprox(
      candles.map((c) => c.high),
      candles.map((c) => c.low),
      candles.map((c) => c.close),
    );
    const avg =
      candles.reduce((s, c) => s + (c.high - c.low), 0) / Math.max(1, candles.length);
    if (atr > avg * 1.4) len = Math.min(12, len + 2);
    if (atr < avg * 0.6) len = Math.max(2, len - 1);
  }

  const sensitivity = settings.sensitivity;
  const minMove =
    atrApprox(
      candles.map((c) => c.high),
      candles.map((c) => c.low),
      candles.map((c) => c.close),
    ) * (0.15 + (1 - sensitivity) * 0.5);

  const swings: SwingPoint[] = [];
  const last = candles.length - 1;

  for (let i = len; i < last - len; i++) {
    let isHigh = true;
    let isLow = true;
    for (let j = 1; j <= len; j++) {
      if (candles[i].high < candles[i - j].high || candles[i].high < candles[i + j].high) {
        isHigh = false;
      }
      if (candles[i].low > candles[i - j].low || candles[i].low > candles[i + j].low) {
        isLow = false;
      }
    }
    if (settings.noiseFilter) {
      if (isHigh) {
        const prevHigh = [...swings].reverse().find((s) => s.kind === "high");
        if (prevHigh && Math.abs(candles[i].high - prevHigh.price) < minMove) isHigh = false;
      }
      if (isLow) {
        const prevLow = [...swings].reverse().find((s) => s.kind === "low");
        if (prevLow && Math.abs(candles[i].low - prevLow.price) < minMove) isLow = false;
      }
    }

    const age = last - i;
    if (isHigh) {
      swings.push({
        id: makeId("sw-"),
        kind: "high",
        index: i,
        time: candles[i].time,
        price: candles[i].high,
        fractal: true,
        ...scoreOf({
          confidence: 55 + sensitivity * 30 - age * 0.2,
          strength: 50 + len * 3,
          ageBars: age,
        }),
        trace: trace("swing.fractal.v1", [i], `len=${len}`),
        createdAt: Date.now(),
      });
    }
    if (isLow) {
      swings.push({
        id: makeId("sw-"),
        kind: "low",
        index: i,
        time: candles[i].time,
        price: candles[i].low,
        fractal: true,
        ...scoreOf({
          confidence: 55 + sensitivity * 30 - age * 0.2,
          strength: 50 + len * 3,
          ageBars: age,
        }),
        trace: trace("swing.fractal.v1", [i], `len=${len}`),
        createdAt: Date.now(),
      });
    }
  }

  return swings.sort((a, b) => a.index - b.index);
}
