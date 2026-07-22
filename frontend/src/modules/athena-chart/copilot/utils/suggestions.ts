import type { AthenaStructuredContext, QuickActionId } from "../types";

/** Suggested follow-up questions derived from structured context (no GPT). */
export function suggestQuestions(ctx: AthenaStructuredContext): string[] {
  const out: string[] = [];
  const o = ctx.opportunity;

  if (o) {
    if (o.confidence < 60) out.push("Why is confidence falling?");
    if (o.direction !== "flat" && o.takeProfit1)
      out.push("Should I secure profits?");
    if (o.opposing.length) out.push("What's invalidating the setup?");
    if (o.bias.includes("buy")) out.push("Why isn't this a stronger buy?");
    if (o.bias.includes("sell")) out.push("Why isn't this a stronger sell?");
    if ((o.mtfConflict ?? 0) > 40) out.push("Why are timeframes conflicting?");
  } else {
    out.push("What is Athena missing to form a trade?");
  }

  if (ctx.liquidity.length) out.push("Where is the nearest liquidity?");
  if (ctx.structure.latestLabels.some((l) => l.includes("BOS")))
    out.push("Explain the latest BOS.");
  if (ctx.liquidity.some((l) => l.kind.includes("sweep")))
    out.push("Explain the liquidity sweep.");
  if (ctx.trend.direction !== "neutral")
    out.push("How strong is this trend?");

  out.push("Should I wait?");
  out.push("What changed recently?");

  return [...new Set(out)].slice(0, 6);
}

export const QUICK_ACTION_LABELS: Record<QuickActionId, string> = {
  explain_chart: "Explain Chart",
  explain_trend: "Explain Trend",
  explain_structure: "Explain Structure",
  why_buy: "Why Buy?",
  why_sell: "Why Sell?",
  current_risks: "Current Risks",
  find_better_entry: "Find Better Entry",
  review_my_trade: "Review My Trade",
  summarize_session: "Summarize Session",
  detect_mistakes: "Detect Mistakes",
  generate_journal: "Generate Journal",
};
