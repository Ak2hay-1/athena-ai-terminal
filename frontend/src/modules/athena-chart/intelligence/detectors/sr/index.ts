import type { Candlestick } from "../../../types";
import type { IntelligenceSettings, PriceLevel, SwingPoint } from "../../types";
import { makeId, scoreOf, trace } from "../../utils/scoring";

export function detectSupportResistance(
  candles: Candlestick[],
  swings: SwingPoint[],
  settings: IntelligenceSettings,
): PriceLevel[] {
  if (!candles.length) return [];
  const atr =
    candles.slice(-20).reduce((s, c) => s + (c.high - c.low), 0) /
    Math.min(20, candles.length);
  const tol = atr * (0.15 + (1 - settings.sensitivity) * 0.25);
  const levels: PriceLevel[] = [];

  const cluster = (kind: "support" | "resistance", points: SwingPoint[]) => {
    const used = new Set<number>();
    for (let i = 0; i < points.length; i++) {
      if (used.has(i)) continue;
      const group = [points[i]];
      used.add(i);
      for (let j = i + 1; j < points.length; j++) {
        if (used.has(j)) continue;
        if (Math.abs(points[j].price - points[i].price) <= tol) {
          group.push(points[j]);
          used.add(j);
        }
      }
      const price = group.reduce((s, p) => s + p.price, 0) / group.length;
      const tests = group.length;
      let retests = 0;
      for (const c of candles.slice(-80)) {
        if (kind === "resistance" && c.high >= price - tol && c.high <= price + tol) retests++;
        if (kind === "support" && c.low <= price + tol && c.low >= price - tol) retests++;
      }
      const last = candles[candles.length - 1].close;
      const broken =
        kind === "resistance" ? last > price + tol : last < price - tol;
      const fresh = retests <= 2;
      const strength = Math.min(100, 40 + tests * 15 + (fresh ? 10 : 0));
      levels.push({
        id: makeId("lvl-"),
        kind,
        price,
        tests,
        fresh,
        broken,
        reactionStrength: strength,
        ...scoreOf({
          confidence: strength * 0.9,
          strength,
          retests,
          status: broken ? "invalid" : "active",
          ageBars: candles.length - 1 - Math.max(...group.map((g) => g.index)),
        }),
        trace: trace(
          "sr.cluster.v1",
          group.map((g) => g.index),
          `${kind}@${price.toFixed(5)}`,
        ),
        createdAt: Date.now(),
      });
    }
  };

  cluster(
    "resistance",
    swings.filter((s) => s.kind === "high"),
  );
  cluster(
    "support",
    swings.filter((s) => s.kind === "low"),
  );

  return levels
    .filter((l) => l.score >= settings.confidenceThreshold * 0.5)
    .sort((a, b) => b.score - a.score)
    .slice(0, 24);
}
