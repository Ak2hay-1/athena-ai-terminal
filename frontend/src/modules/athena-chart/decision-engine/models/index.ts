import type { TradeOpportunity } from "../types";

export function recommendedAction(opp: TradeOpportunity | null): string {
  if (!opp) return "Wait for analysis";
  if (opp.exit.action === "close_trade") return `Close — ${opp.exit.reason}`;
  if (opp.exit.action === "partial_exit")
    return `Partial exit ${opp.exit.partialPct ?? 30}% — ${opp.exit.reason}`;
  if (opp.exit.action === "move_stop_loss")
    return `Trail SL — ${opp.exit.reason}`;
  switch (opp.bias) {
    case "strong_buy":
      return "Strong Buy — enter on pullback to zone";
    case "buy":
      return "Buy — balanced entry preferred";
    case "watch_buy":
      return "Watch Buy — wait for confirmation";
    case "strong_sell":
      return "Strong Sell — enter on rally into supply";
    case "sell":
      return "Sell — balanced entry preferred";
    case "watch_sell":
      return "Watch Sell — wait for confirmation";
    default:
      return "Neutral — no trade";
  }
}

export function formatBiasLabel(bias: string): string {
  return bias.replace(/_/g, " ");
}
