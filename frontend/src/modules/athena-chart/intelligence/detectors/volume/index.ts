import type { Candlestick } from "../../../types";
import type { VolumeIntel } from "../../types";

export function analyzeVolume(candles: Candlestick[]): VolumeIntel {
  if (candles.length < 20) {
    return {
      participation: "normal",
      pressure: "balanced",
      absorption: false,
      exhaustion: false,
      climax: false,
      divergence: false,
      score: 50,
    };
  }
  const recent = candles.slice(-20);
  const avg =
    candles.slice(-60).reduce((s, c) => s + c.tick_volume, 0) /
    Math.min(60, candles.length);
  const last = recent[recent.length - 1];
  const volAvg = recent.reduce((s, c) => s + c.tick_volume, 0) / recent.length;
  const participation =
    volAvg > avg * 1.35 ? "high" : volAvg < avg * 0.65 ? "low" : "normal";

  let upVol = 0;
  let downVol = 0;
  for (const c of recent) {
    if (c.close >= c.open) upVol += c.tick_volume;
    else downVol += c.tick_volume;
  }
  const pressure =
    upVol > downVol * 1.15
      ? "buying"
      : downVol > upVol * 1.15
        ? "selling"
        : "balanced";

  const climax = last.tick_volume > avg * 2.5;
  const absorption =
    last.tick_volume > avg * 1.8 &&
    Math.abs(last.close - last.open) < (last.high - last.low) * 0.25;
  const exhaustion =
    climax &&
    ((pressure === "buying" && last.close < last.open) ||
      (pressure === "selling" && last.close > last.open));

  // Price up / volume down divergence
  const priceUp = last.close > recent[0].close;
  const volDown = last.tick_volume < recent[0].tick_volume;
  const divergence = (priceUp && volDown && pressure !== "buying") || (!priceUp && !volDown);

  const score =
    40 +
    (participation === "high" ? 15 : 0) +
    (absorption ? 10 : 0) +
    (climax ? 10 : 0) -
    (exhaustion ? 10 : 0);

  return {
    participation,
    pressure,
    absorption,
    exhaustion,
    climax,
    divergence,
    score: Math.max(0, Math.min(100, score)),
  };
}
