import type { Candlestick } from "../../../types";
import type { StructureEvent, SwingPoint } from "../../types";
import { makeId, scoreOf, trace } from "../../utils/scoring";

/** HH/HL/LH/LL + BOS/CHOCH from swing sequence. */
export function detectStructure(
  candles: Candlestick[],
  swings: SwingPoint[],
): StructureEvent[] {
  const events: StructureEvent[] = [];
  const highs = swings.filter((s) => s.kind === "high");
  const lows = swings.filter((s) => s.kind === "low");

  for (let i = 1; i < highs.length; i++) {
    const prev = highs[i - 1];
    const cur = highs[i];
    const label = cur.price > prev.price ? "HH" : "LH";
    events.push(structEvent(label, cur, cur.price > prev.price ? "bullish" : "bearish", "external"));
  }
  for (let i = 1; i < lows.length; i++) {
    const prev = lows[i - 1];
    const cur = lows[i];
    const label = cur.price > prev.price ? "HL" : "LL";
    events.push(structEvent(label, cur, cur.price > prev.price ? "bullish" : "bearish", "external"));
  }

  // BOS / CHOCH on last swings vs recent close breaks
  if (candles.length < 3 || swings.length < 3) return events;
  const last = candles.length - 1;
  const close = candles[last].close;
  const recentHigh = [...highs].reverse()[0];
  const recentLow = [...lows].reverse()[0];
  const priorHigh = [...highs].reverse()[1];
  const priorLow = [...lows].reverse()[1];

  if (recentHigh && priorHigh) {
    if (close > recentHigh.price && recentHigh.price > priorHigh.price) {
      events.push(
        structEvent("BOS", recentHigh, "bullish", "external", last, candles[last].time, close),
      );
    } else if (close > recentHigh.price && recentHigh.price < priorHigh.price) {
      events.push(
        structEvent("CHOCH", recentHigh, "bullish", "external", last, candles[last].time, close),
      );
    }
  }
  if (recentLow && priorLow) {
    if (close < recentLow.price && recentLow.price < priorLow.price) {
      events.push(
        structEvent("BOS", recentLow, "bearish", "external", last, candles[last].time, close),
      );
    } else if (close < recentLow.price && recentLow.price > priorLow.price) {
      events.push(
        structEvent("CHOCH", recentLow, "bearish", "external", last, candles[last].time, close),
      );
    }
  }

  // Internal: use half the swings
  const mid = Math.floor(swings.length / 2);
  const internal = swings.slice(mid);
  for (let i = 1; i < internal.length; i++) {
    const a = internal[i - 1];
    const b = internal[i];
    if (a.kind === b.kind) continue;
    if (b.kind === "high" && a.kind === "low") {
      events.push(structEvent(b.price > a.price ? "HH" : "LH", b, b.price > a.price ? "bullish" : "bearish", "internal"));
    }
  }

  return events;
}

function structEvent(
  label: StructureEvent["label"],
  swing: SwingPoint,
  direction: "bullish" | "bearish",
  scope: "internal" | "external",
  index = swing.index,
  time = swing.time,
  price = swing.price,
): StructureEvent {
  return {
    id: makeId("st-"),
    label,
    index,
    time,
    price,
    direction,
    scope,
    ...scoreOf({
      confidence: label === "BOS" || label === "CHOCH" ? 75 : 60,
      strength: scope === "external" ? 70 : 50,
      ageBars: 0,
    }),
    trace: trace("structure.swing.v1", [swing.index, index], label),
    createdAt: Date.now(),
  };
}
