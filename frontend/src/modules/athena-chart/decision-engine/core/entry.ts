import type { Candlestick } from "../../types";
import type { AnalysisSnapshot } from "../../intelligence/types";
import { computeAtr } from "../../engine/indicators/calculations";
import type {
  DecisionSettings,
  EntryPlan,
  EntryStyle,
} from "../types";
import { resolveProfile, riskModeMultiplier } from "../strategies/profiles";
import { clamp, lastFinite, roundPrice } from "../utils/math";

function buildOne(
  style: EntryStyle,
  direction: "long" | "short",
  price: number,
  atr: number,
  settings: DecisionSettings,
  structureStop?: number,
): EntryPlan {
  const profile = resolveProfile(settings);
  const mode = riskModeMultiplier(settings.riskMode);

  const styleSl =
    style === "conservative" ? 1.25 : style === "aggressive" ? 0.8 : 1;
  const styleTp =
    style === "conservative" ? 0.9 : style === "aggressive" ? 1.15 : 1;

  const slDist = atr * profile.slAtrMult * mode.sl * styleSl;
  let stopLoss =
    direction === "long" ? price - slDist : price + slDist;

  if (structureStop != null && Number.isFinite(structureStop)) {
    if (direction === "long") {
      stopLoss = Math.min(stopLoss, structureStop - atr * 0.15);
    } else {
      stopLoss = Math.max(stopLoss, structureStop + atr * 0.15);
    }
  }

  const risk = Math.abs(price - stopLoss) || atr * 0.5;
  const tp1 =
    direction === "long"
      ? price + atr * profile.tp1AtrMult * styleTp
      : price - atr * profile.tp1AtrMult * styleTp;
  const tp2 =
    direction === "long"
      ? price + atr * profile.tp2AtrMult * styleTp
      : price - atr * profile.tp2AtrMult * styleTp;
  const tp3 =
    direction === "long"
      ? price + atr * profile.tp3AtrMult * styleTp
      : price - atr * profile.tp3AtrMult * styleTp;

  const rr = Math.abs(tp1 - price) / risk;

  // Entry offset by style
  const entryOffset =
    style === "conservative"
      ? atr * 0.15 * (direction === "long" ? -1 : 1)
      : style === "aggressive"
        ? atr * 0.05 * (direction === "long" ? 1 : -1)
        : 0;
  const entry = price + entryOffset;

  return {
    style,
    entry: roundPrice(entry),
    stopLoss: roundPrice(stopLoss),
    takeProfit1: roundPrice(tp1),
    takeProfit2: roundPrice(tp2),
    takeProfit3: roundPrice(tp3),
    riskReward: Math.round(rr * 100) / 100,
    atrDistance: roundPrice(atr),
    maximumRisk: roundPrice(risk),
  };
}

export function generateEntries(
  candles: Candlestick[],
  analysis: AnalysisSnapshot,
  direction: "long" | "short" | "flat",
  settings: DecisionSettings,
): EntryPlan[] {
  if (direction === "flat" || !candles.length) return [];
  const price = candles[candles.length - 1].close;
  const atrSeries = computeAtr(candles);
  const atr = lastFinite(atrSeries) ?? price * 0.002;

  // Prefer structure swing for stop
  const swings = analysis.swings;
  let structureStop: number | undefined;
  if (direction === "long") {
    const lows = swings.filter((s) => s.kind === "low").slice(-3);
    structureStop = lows.length
      ? Math.min(...lows.map((s) => s.price))
      : undefined;
  } else {
    const highs = swings.filter((s) => s.kind === "high").slice(-3);
    structureStop = highs.length
      ? Math.max(...highs.map((s) => s.price))
      : undefined;
  }

  const styles: EntryStyle[] = ["conservative", "balanced", "aggressive"];
  return styles.map((style) =>
    buildOne(style, direction, price, atr, settings, structureStop),
  );
}

export function pickActiveEntry(
  entries: EntryPlan[],
  preferred: EntryStyle,
): EntryPlan | null {
  return entries.find((e) => e.style === preferred) ?? entries[1] ?? entries[0] ?? null;
}

export function zonesFromAnalysis(
  analysis: AnalysisSnapshot,
  direction: "long" | "short" | "flat",
): {
  buyZone: { top: number; bottom: number } | null;
  sellZone: { top: number; bottom: number } | null;
} {
  const demand = analysis.zones
    .filter((z) => z.kind === "demand" && z.status === "active")
    .sort((a, b) => b.score - a.score)[0];
  const supply = analysis.zones
    .filter((z) => z.kind === "supply" && z.status === "active")
    .sort((a, b) => b.score - a.score)[0];
  const bullOb = analysis.orderBlocks
    .filter((o) => o.bias === "bullish" && o.status === "active")
    .sort((a, b) => b.score - a.score)[0];
  const bearOb = analysis.orderBlocks
    .filter((o) => o.bias === "bearish" && o.status === "active")
    .sort((a, b) => b.score - a.score)[0];

  let buyZone: { top: number; bottom: number } | null = null;
  let sellZone: { top: number; bottom: number } | null = null;

  if (direction === "long" || direction === "flat") {
    if (demand) buyZone = { top: demand.top, bottom: demand.bottom };
    else if (bullOb) buyZone = { top: bullOb.top, bottom: bullOb.bottom };
  }
  if (direction === "short" || direction === "flat") {
    if (supply) sellZone = { top: supply.top, bottom: supply.bottom };
    else if (bearOb) sellZone = { top: bearOb.top, bottom: bearOb.bottom };
  }

  return { buyZone, sellZone };
}

export function meetsRrFilter(entry: EntryPlan | null, minRr: number): boolean {
  if (!entry) return false;
  return entry.riskReward >= minRr;
}

export function clampRrDisplay(rr: number): number {
  return clamp(rr, 0, 20);
}
