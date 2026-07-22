import { chatWithAthena } from "@/services/ai";
import type { AIProvider } from "./types";
import type { AiCompletionRequest, AiCompletionResult } from "../../types";

/** Azure OpenAI via Athena backend `/ai/chat` (keys never leave the server). */
export class AzureOpenAIProvider implements AIProvider {
  readonly id = "azure" as const;

  async complete(req: AiCompletionRequest): Promise<AiCompletionResult> {
    try {
      const result = await chatWithAthena({
        messages: req.messages.map((m) => ({
          role: m.role === "system" ? "system" : m.role,
          content: m.content,
        })),
        symbol: req.symbol,
        timeframe: req.timeframe,
      });
      return {
        success: result.success,
        content: result.reply || result.message || "",
        provider: "azure",
        model: result.model ?? "gpt-5-mini",
        message: result.message ?? undefined,
      };
    } catch (err) {
      return {
        success: false,
        content: "",
        provider: "azure",
        model: "gpt-5-mini",
        message: err instanceof Error ? err.message : "Azure provider failed",
      };
    }
  }
}
