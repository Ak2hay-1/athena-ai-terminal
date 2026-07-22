import type { AIProvider } from "./types";
import type { AiCompletionRequest, AiCompletionResult } from "../../types";

/**
 * Deterministic mock — explains only from structured context embedded in the prompt.
 * Used offline / when GPT is unavailable. Never invents prices or signals.
 */
export class MockProvider implements AIProvider {
  readonly id = "mock" as const;

  async complete(req: AiCompletionRequest): Promise<AiCompletionResult> {
    const system = req.messages.find((m) => m.role === "system")?.content ?? "";
    const user = [...req.messages].reverse().find((m) => m.role === "user")?.content ?? "";
    const content = buildMockReply(system, user);
    return {
      success: true,
      content,
      provider: "mock",
      model: "athena-mock-v1",
      fromCache: false,
    };
  }
}

function pick(block: string, key: string): string | null {
  const re = new RegExp(`${key}:\\s*(.+)`, "i");
  const m = block.match(re);
  return m?.[1]?.trim() ?? null;
}

function buildMockReply(system: string, user: string): string {
  const symbol = pick(system, "Current Symbol") ?? "unknown";
  const tf = pick(system, "Timeframe") ?? "—";
  const trend = pick(system, "Trend") ?? "unavailable";
  const confidence = pick(system, "Confidence") ?? "n/a";
  const grade = pick(system, "Trade Grade") ?? "n/a";
  const bias = pick(system, "Opportunity") ?? "neutral";
  const structure = pick(system, "Current Structure") ?? "not available";
  const supporting = pick(system, "Supporting") ?? "none listed";
  const opposing = pick(system, "Opposing") ?? "none listed";
  const risks = pick(system, "Risk Notes") ?? "not available";
  const gaps = pick(system, "Data Gaps");

  if (gaps && gaps !== "none") {
    return (
      `I can only explain what Athena's engines reported.\n\n` +
      `Missing data: ${gaps}\n\n` +
      `Available: ${symbol} ${tf} · trend ${trend} · opportunity ${bias} · confidence ${confidence}.`
    );
  }

  const q = user.toLowerCase();
  if (q.includes("risk")) {
    return (
      `Current risks for ${symbol} (${tf}) per Decision Engine:\n` +
      `• Opportunity: ${bias} · Grade ${grade} · Confidence ${confidence}\n` +
      `• Risk notes: ${risks}\n` +
      `• Conflicting signals: ${opposing}\n\n` +
      `I am not inventing levels — only restating Athena's structured risk fields.`
    );
  }
  if (q.includes("why buy") || q.includes("why.*buy") || q.includes("buy?")) {
    return (
      `Why a buy bias may apply (${symbol} ${tf}) — Decision Engine references only:\n` +
      `• Opportunity: ${bias} · Grade ${grade}\n` +
      `• Confidence: ${confidence}\n` +
      `• Supporting: ${supporting}\n` +
      `• Structure: ${structure}\n\n` +
      `If opportunity is not buy/strong_buy, Athena is not recommending a long.`
    );
  }
  if (q.includes("why sell") || q.includes("sell?")) {
    return (
      `Why a sell bias may apply (${symbol} ${tf}):\n` +
      `• Opportunity: ${bias} · Grade ${grade}\n` +
      `• Confidence: ${confidence}\n` +
      `• Supporting: ${supporting}\n` +
      `• Opposing: ${opposing}`
    );
  }
  if (q.includes("structure") || q.includes("bos") || q.includes("trend")) {
    return (
      `${symbol} ${tf} structure/trend explanation (Intelligence Engine):\n` +
      `• Trend: ${trend}\n` +
      `• Structure: ${structure}\n` +
      `• Opportunity bias: ${bias} · Confidence ${confidence}\n\n` +
      `No raw candles were used — only scored structure labels.`
    );
  }

  return (
    `Athena Copilot (mock) — ${symbol} ${tf}\n\n` +
    `Trend: ${trend}\n` +
    `Structure: ${structure}\n` +
    `Opportunity: ${bias} · Grade ${grade} · Confidence ${confidence}\n` +
    `Supporting: ${supporting}\n` +
    `Opposing: ${opposing}\n` +
    `Risks: ${risks}\n\n` +
    `Question: ${user}\n\n` +
    `This reply only restates Decision/Intelligence engine fields. ` +
    `Connect Azure OpenAI on the backend for richer coaching language.`
  );
}
