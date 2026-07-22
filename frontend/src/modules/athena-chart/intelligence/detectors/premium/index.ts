import type { PremiumDiscount, SwingPoint } from "../../types";

export function computePremiumDiscount(swings: SwingPoint[]): PremiumDiscount | null {
  const highs = swings.filter((s) => s.kind === "high");
  const lows = swings.filter((s) => s.kind === "low");
  if (!highs.length || !lows.length) return null;
  const swingHigh = Math.max(...highs.slice(-5).map((s) => s.price));
  const swingLow = Math.min(...lows.slice(-5).map((s) => s.price));
  if (swingHigh <= swingLow) return null;
  const eq = (swingHigh + swingLow) / 2;
  const midHigh = eq + (swingHigh - eq) * 0.5;
  return {
    equilibrium: eq,
    premiumHigh: swingHigh,
    premiumLow: midHigh,
    discountHigh: eq - (eq - swingLow) * 0.0,
    discountLow: swingLow,
    swingHigh,
    swingLow,
  };
}
