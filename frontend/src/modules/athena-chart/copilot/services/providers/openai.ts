import { chatWithAthena } from "@/services/ai";
import type { AIProvider } from "./types";
import type { AiCompletionRequest, AiCompletionResult } from "../../types";

/**
 * OpenAI API path — still routed through Athena backend so client has no keys.
 * Backend selects provider via AI_PROVIDER; this tags requests for OpenAI-style chat.
 */
export class OpenAIProvider implements AIProvider {
  readonly id = "openai" as const;

  async complete(req: AiCompletionRequest): Promise<AiCompletionResult> {
    try {
      const result = await chatWithAthena({
        messages: [
          {
            role: "system",
            content:
              "Provider preference: openai. Follow Athena structured context strictly.",
          },
          ...req.messages.map((m) => ({
            role: m.role === "system" ? ("system" as const) : m.role,
            content: m.content,
          })),
        ],
        symbol: req.symbol,
        timeframe: req.timeframe,
      });
      return {
        success: result.success,
        content: result.reply || result.message || "",
        provider: "openai",
        model: result.model ?? "gpt-4o-mini",
        message: result.message ?? undefined,
      };
    } catch (err) {
      return {
        success: false,
        content: "",
        provider: "openai",
        model: "gpt-4o-mini",
        message: err instanceof Error ? err.message : "OpenAI provider failed",
      };
    }
  }
}
