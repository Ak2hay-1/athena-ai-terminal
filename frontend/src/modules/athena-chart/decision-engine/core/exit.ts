import type { AnalysisSnapshot } from "../../intelligence/types";
import type { Candlestick } from "../../types";
import type {
  ExitRecommendation,
  TradeOpportunity,
} from "../types";

/** Continuously monitor open opportunity against latest analysis. */
export function evaluateExit(
  candles: Candlestick[],
  analysis: AnalysisSnapshot,
  opportunity: TradeOpportunity | null,
): ExitRecommendation {
  if (!opportunity || opportunity.direction === "flat") {
    return { action: "hold", reason: "No active directional trade" };
  }
  if (!candles.length) {
    return { action: "hold", reason: "Insufficient data" };
  }

  const price = candles[candles.length - 1].close;
  const entry = opportunity.activeEntry;
  const dir = opportunity.direction;

  // TP / SL checks
  if (dir === "long") {
    if (price <= entry.stopLoss) {
      return { action: "close_trade", reason: "Stop loss reached" };
    }
    if (price >= entry.takeProfit3) {
      return { action: "close_trade", reason: "TP3 reached" };
    }
    if (price >= entry.takeProfit2) {
      return {
        action: "move_stop_loss",
        reason: "TP2 reached — trail stop to entry",
        suggestedStop: entry.entry,
        partialPct: 50,
      };
    }
    if (price >= entry.takeProfit1) {
      return {
        action: "partial_exit",
        reason: "TP1 reached",
        suggestedStop: entry.entry,
        partialPct: 33,
      };
    }
  } else {
    if (price >= entry.stopLoss) {
      return { action: "close_trade", reason: "Stop loss reached" };
    }
    if (price <= entry.takeProfit3) {
      return { action: "close_trade", reason: "TP3 reached" };
    }
    if (price <= entry.takeProfit2) {
      return {
        action: "move_stop_loss",
        reason: "TP2 reached — trail stop to entry",
        suggestedStop: entry.entry,
        partialPct: 50,
      };
    }
    if (price <= entry.takeProfit1) {
      return {
        action: "partial_exit",
        reason: "TP1 reached",
        suggestedStop: entry.entry,
        partialPct: 33,
      };
    }
  }

  // Weakening trend
  const trendDir = analysis.trend.direction;
  if (
    (dir === "long" && trendDir === "bearish") ||
    (dir === "short" && trendDir === "bullish")
  ) {
    if (analysis.trend.confidence >= 55) {
      return { action: "close_trade", reason: "Trend flipped against position" };
    }
    return {
      action: "partial_exit",
      reason: "Trend weakening",
      partialPct: 25,
    };
  }

  // Structure break (CHOCH against)
  const lastStruct = analysis.structure[analysis.structure.length - 1];
  if (
    lastStruct &&
    lastStruct.label === "CHOCH" &&
    ((dir === "long" && lastStruct.direction === "bearish") ||
      (dir === "short" && lastStruct.direction === "bullish"))
  ) {
    return { action: "close_trade", reason: "Adverse CHOCH" };
  }

  // Liquidity target
  const sweep = analysis.liquidity.find((l) =>
    l.kind.includes("sweep") || l.kind.includes("hunt"),
  );
  if (sweep && sweep.importance >= 70) {
    const nearTarget =
      dir === "long"
        ? Math.abs(price - entry.takeProfit1) / price < 0.002
        : Math.abs(price - entry.takeProfit1) / price < 0.002;
    if (nearTarget) {
      return {
        action: "partial_exit",
        reason: "Liquidity target approached",
        partialPct: 40,
      };
    }
  }

  // Volume exhaustion
  if (analysis.volume.exhaustion) {
    return {
      action: "partial_exit",
      reason: "Volume exhaustion",
      partialPct: 30,
    };
  }

  // Opposite order block
  const oppositeOb = analysis.orderBlocks.find(
    (o) =>
      o.status === "active" &&
      ((dir === "long" && o.bias === "bearish") ||
        (dir === "short" && o.bias === "bullish")) &&
      price <= o.top &&
      price >= o.bottom,
  );
  if (oppositeOb) {
    return {
      action: "move_stop_loss",
      reason: "Approaching opposite order block",
      suggestedStop:
        dir === "long"
          ? Math.max(entry.stopLoss, oppositeOb.bottom)
          : Math.min(entry.stopLoss, oppositeOb.top),
    };
  }

  return { action: "hold", reason: "Setup intact" };
}
