import type {
  AthenaStructuredContext,
  PromptPacket,
  QuickActionId,
  SummaryHorizon,
} from "../types";
import { contextHash } from "../context/builder";
import { SAFETY_SYSTEM_RULES } from "./safety";

const ACTION_PROMPTS: Record<QuickActionId, string> = {
  explain_chart:
    "Explain the current chart state using only the structured Athena context. Cover trend, structure, liquidity, and the active Decision Engine opportunity.",
  explain_trend:
    "Explain the current trend classification and confidence. Reference only Athena trend + MTF fields.",
  explain_structure:
    "Explain the latest market structure labels (HH/HL/LH/LL/BOS/CHOCH). Do not invent swings.",
  why_buy:
    "Explain whether a buy is justified using Decision Engine supporting signals, grade, and probability. If bias is not buy-side, say so clearly.",
  why_sell:
    "Explain whether a sell is justified using Decision Engine supporting signals. If bias is not sell-side, say so clearly.",
  current_risks:
    "List current risks from Decision Engine risk notes, opposing signals, and risk category. No invented levels.",
  find_better_entry:
    "Using Decision Engine entry styles and zones already present, discuss whether a better entry exists. Do not invent new prices.",
  review_my_trade:
    "Review the active or last trade plan (entry/SL/TP/exit) from Decision Engine fields only.",
  summarize_session:
    "Write a concise session summary from trend, structure, sessions, and opportunity fields.",
  detect_mistakes:
    "Identify potential mistakes relative to Athena's plan (early entry, ignoring opposing signals, poor RR). Stay grounded in context.",
  generate_journal:
    "Draft a journal entry summarizing setup, rationale, risk, and lesson — only from structured fields.",
};

export function buildPromptPacket(opts: {
  ctx: AthenaStructuredContext;
  question: string;
  maxTokens?: number;
}): PromptPacket {
  const { ctx, question } = opts;
  const maxTokens = opts.maxTokens ?? 1800;
  const structured = serializeContext(ctx, maxTokens);
  const system = [
    SAFETY_SYSTEM_RULES,
    "",
    "=== ATHENA STRUCTURED CONTEXT (authoritative) ===",
    structured,
    "=== END CONTEXT ===",
  ].join("\n");

  return {
    system,
    user: question.trim(),
    estimatedTokens: estimateTokens(system) + estimateTokens(question),
    contextHash: contextHash(ctx),
  };
}

export function promptForQuickAction(
  ctx: AthenaStructuredContext,
  action: QuickActionId,
): PromptPacket {
  return buildPromptPacket({
    ctx,
    question: ACTION_PROMPTS[action],
  });
}

export function promptForClickExplain(
  ctx: AthenaStructuredContext,
): PromptPacket {
  const obj = ctx.selectedObject;
  const q = obj
    ? `Explain the selected chart object: ${obj.kind} — ${obj.label}. Use Athena engines only.`
    : "Explain the currently focused chart element. If none is selected, say so.";
  return buildPromptPacket({ ctx, question: q });
}

export function promptForSummary(
  ctx: AthenaStructuredContext,
  horizon: SummaryHorizon,
): PromptPacket {
  const labels: Record<SummaryHorizon, string> = {
    "1m": "1-minute",
    "5m": "5-minute",
    "1h": "hourly",
    session: "session",
    daily: "daily",
    weekly: "weekly",
  };
  return buildPromptPacket({
    ctx,
    question: `Generate a ${labels[horizon]} market summary. Prefer institutional language. Reference confidence and preferred direction only if present in context.`,
  });
}

export function promptForCoach(ctx: AthenaStructuredContext): PromptPacket {
  return buildPromptPacket({
    ctx,
    question:
      "Act as a trading coach. Review risk management, position sizing hints, stop placement, take profits, holding time, and overtrading risks using Athena Decision Engine fields. Do not invent a new trade.",
  });
}

export function promptForTradeReview(ctx: AthenaStructuredContext): PromptPacket {
  return buildPromptPacket({
    ctx,
    question:
      "Produce a post-trade review: entry review, exit review, mistakes, strengths, alternative management, lesson learned, journal summary. Use only available Decision Engine / opportunity fields. If trade data is incomplete, state the gaps.",
  });
}

function serializeContext(ctx: AthenaStructuredContext, maxTokens: number): string {
  const lines: string[] = [
    `Current Symbol: ${ctx.symbol}`,
    `Timeframe: ${ctx.timeframe}`,
    `Trend: ${ctx.trend.classification} (${ctx.trend.direction}, conf ${Math.round(ctx.trend.confidence)})`,
    `Current Structure: ${ctx.structure.latestLabels.join(", ") || "none"}`,
    `Structure Bias: ${ctx.structure.bias}`,
  ];

  if (ctx.liquidity.length) {
    lines.push(
      `Liquidity: ${ctx.liquidity
        .map((l) => `${l.kind}@${l.price}(imp${l.importance})`)
        .join("; ")}`,
    );
  }
  if (ctx.orderBlocks.length) {
    lines.push(
      `Order Blocks: ${ctx.orderBlocks
        .map((o) => `${o.bias} score${o.score} [${o.bottom}-${o.top}]`)
        .join("; ")}`,
    );
  }
  if (ctx.fvgs.length) {
    lines.push(
      `FVG: ${ctx.fvgs.map((f) => `${f.bias} ${f.status} fill${f.fillRatio}`).join("; ")}`,
    );
  }

  lines.push(
    `Volume: ${ctx.volume.participation}/${ctx.volume.pressure}${
      ctx.volume.flags.length ? ` [${ctx.volume.flags.join(",")}]` : ""
    }`,
  );

  if (ctx.sessions.length) {
    lines.push(
      `Sessions: ${ctx.sessions
        .map((s) => `${s.name}${s.active ? "*" : ""}${s.killZone ? "(KZ)" : ""}`)
        .join(", ")}`,
    );
  }

  lines.push(
    `Confluence: B${ctx.confluence.bullish}/S${ctx.confluence.bearish}/N${ctx.confluence.neutral} conf${ctx.confluence.confidence}`,
  );
  if (ctx.confluence.drivers.length) {
    lines.push(`Drivers: ${ctx.confluence.drivers.join(", ")}`);
  }

  const o = ctx.opportunity;
  if (o) {
    lines.push(`Opportunity: ${o.bias}`);
    lines.push(`Trade Grade: ${o.grade}`);
    lines.push(`Confidence: ${o.confidence}% (${o.confidenceLabel})`);
    lines.push(
      `Probability: bull ${o.probability.bullish}% / bear ${o.probability.bearish}% / neut ${o.probability.neutral}%`,
    );
    if (o.entry != null) lines.push(`Entry: ${o.entry}`);
    if (o.stopLoss != null) lines.push(`Stop Loss: ${o.stopLoss}`);
    if (o.takeProfit1 != null) {
      lines.push(`TP: ${o.takeProfit1} / ${o.takeProfit2} / ${o.takeProfit3}`);
    }
    if (o.riskReward != null) lines.push(`Risk Reward: ${o.riskReward}`);
    if (o.riskCategory) lines.push(`Risk Category: ${o.riskCategory}`);
    lines.push(`Supporting: ${o.supporting.join("; ") || "none"}`);
    lines.push(`Opposing: ${o.opposing.join("; ") || "none"}`);
    lines.push(`Risk Notes: ${(o.explanationRisks ?? []).join("; ") || "none"}`);
    if (o.explanationSummary) lines.push(`Decision Summary: ${o.explanationSummary}`);
    if (o.exitAction) lines.push(`Exit: ${o.exitAction} — ${o.exitReason}`);
    if (o.mtfAlignment != null) {
      lines.push(
        `MTF: align ${o.mtfAlignment}% conflict ${o.mtfConflict}% dominant ${o.mtfDominant}`,
      );
    }
  } else {
    lines.push("Opportunity: unavailable");
  }

  const ind = ctx.indicators;
  lines.push(
    `Indicators: RSI=${ind.rsi ?? "n/a"} MACDhist=${ind.macdHist ?? "n/a"} VWAP=${ind.vwapBias ?? "n/a"} ATR=${ind.atr ?? "n/a"}`,
  );

  if (ctx.selectedObject) {
    lines.push(
      `Selected Object: ${ctx.selectedObject.kind} — ${ctx.selectedObject.label}` +
        (ctx.selectedObject.price != null ? ` @ ${ctx.selectedObject.price}` : ""),
    );
  }

  if (ctx.recentDecisions.length) {
    lines.push(`Recent AI Decisions: ${ctx.recentDecisions.join(" | ")}`);
  }
  if (ctx.news?.length) {
    lines.push(
      `News: ${ctx.news.map((n) => `${n.title}(${n.impact})`).join("; ")}`,
    );
  }
  if (ctx.positions?.length) {
    lines.push(
      `Positions: ${ctx.positions
        .map((p) => `${p.side}@${p.entry}`)
        .join("; ")}`,
    );
  }
  if (ctx.journalNotes?.length) {
    lines.push(`Journal: ${ctx.journalNotes.join(" | ")}`);
  }

  lines.push(
    `Data Gaps: ${ctx.dataGaps.length ? ctx.dataGaps.join(", ") : "none"}`,
  );

  let text = lines.join("\n");
  // Token budget: truncate least critical tails
  while (estimateTokens(text) > maxTokens * 0.7 && lines.length > 12) {
    lines.splice(Math.floor(lines.length * 0.6), 1);
    text = lines.join("\n");
  }
  return text;
}

export function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4);
}

export { ACTION_PROMPTS };
