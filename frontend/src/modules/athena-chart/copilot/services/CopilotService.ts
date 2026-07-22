import type {
  AthenaStructuredContext,
  CopilotMessage,
  PromptPacket,
  QuickActionId,
  SummaryHorizon,
} from "../types";
import { CopilotAgents } from "../agents";
import { completeWithFallback } from "./providers/factory";
import { appendSafetyFooter, validateCopilotReply } from "../utils/safety";
import { mayCallGpt, type CopilotTrigger } from "../utils/costGate";
import type { AiProviderId } from "../types";
import { uid } from "../utils/id";

export class CopilotService {
  private cache = new Map<string, { at: number; content: string; provider: AiProviderId; model: string }>();
  private lastContextHash = "";

  async run(opts: {
    ctx: AthenaStructuredContext;
    packet: PromptPacket;
    provider: AiProviderId;
    trigger: CopilotTrigger;
    history?: CopilotMessage[];
    metaAction?: CopilotMessage["meta"];
  }): Promise<CopilotMessage> {
    if (!mayCallGpt(opts.trigger)) {
      return assistantMsg(
        "GPT call blocked by cost gate (not a permitted trigger).",
        { provider: "mock", model: "cost-gate" },
      );
    }

    const cacheKey = `${opts.packet.contextHash}:${hashStr(opts.packet.user)}:${opts.provider}`;
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.at < 120_000) {
      return assistantMsg(cached.content, {
        ...opts.metaAction,
        provider: cached.provider,
        model: cached.model,
        fromCache: true,
      });
    }

    const historyMsgs = (opts.history ?? [])
      .filter((m) => m.role !== "system")
      .slice(-6)
      .map((m) => ({ role: m.role, content: m.content }));

    const result = await completeWithFallback(opts.provider, {
      messages: [
        { role: "system", content: opts.packet.system },
        ...historyMsgs,
        { role: "user", content: opts.packet.user },
      ],
      symbol: opts.ctx.symbol,
      timeframe: opts.ctx.timeframe,
      maxTokens: 700,
    });

    let content = result.content?.trim() || result.message || "No response.";
    if (!result.success && !content) {
      content = "Copilot could not reach the AI provider. Showing grounded mock fallback is recommended.";
    }

    const validation = validateCopilotReply(content, opts.ctx);
    if (!validation.ok) {
      content += `\n\n—\nSafety note: ${validation.warnings.join("; ")}`;
    }
    content = appendSafetyFooter(content, opts.ctx);

    this.cache.set(cacheKey, {
      at: Date.now(),
      content,
      provider: result.provider,
      model: result.model,
    });
    this.lastContextHash = opts.packet.contextHash;

    return assistantMsg(content, {
      ...opts.metaAction,
      provider: result.provider,
      model: result.model,
      fromCache: result.fromCache,
    });
  }

  ask(ctx: AthenaStructuredContext, question: string, provider: AiProviderId, history?: CopilotMessage[]) {
    return this.run({
      ctx,
      packet: CopilotAgents.qa(ctx, question),
      provider,
      trigger: "user_question",
      history,
      metaAction: { action: "qa" },
    });
  }

  quickAction(
    ctx: AthenaStructuredContext,
    action: QuickActionId,
    provider: AiProviderId,
    history?: CopilotMessage[],
  ) {
    return this.run({
      ctx,
      packet: CopilotAgents.quick(ctx, action),
      provider,
      trigger: "quick_action",
      history,
      metaAction: { action },
    });
  }

  explainClick(ctx: AthenaStructuredContext, provider: AiProviderId) {
    return this.run({
      ctx,
      packet: CopilotAgents.explainObject(ctx),
      provider,
      trigger: "click_explain",
      metaAction: { action: "click_explain" },
    });
  }

  summarize(
    ctx: AthenaStructuredContext,
    horizon: SummaryHorizon,
    provider: AiProviderId,
  ) {
    return this.run({
      ctx,
      packet: CopilotAgents.summary(ctx, horizon),
      provider,
      trigger: "user_question",
      metaAction: { action: "summary" },
    });
  }

  coach(ctx: AthenaStructuredContext, provider: AiProviderId) {
    return this.run({
      ctx,
      packet: CopilotAgents.coach(ctx),
      provider,
      trigger: "user_question",
      metaAction: { action: "coach" },
    });
  }

  review(ctx: AthenaStructuredContext, provider: AiProviderId) {
    return this.run({
      ctx,
      packet: CopilotAgents.review(ctx),
      provider,
      trigger: "trade_close",
      metaAction: { action: "review" },
    });
  }

  getLastContextHash(): string {
    return this.lastContextHash;
  }
}

function assistantMsg(
  content: string,
  meta?: CopilotMessage["meta"],
): CopilotMessage {
  return {
    id: uid("msg"),
    role: "assistant",
    content,
    createdAt: Date.now(),
    meta,
  };
}

function hashStr(s: string): string {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36);
}

let singleton: CopilotService | null = null;
export function getCopilotService(): CopilotService {
  if (!singleton) singleton = new CopilotService();
  return singleton;
}
