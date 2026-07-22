import type { AIProvider } from "./types";
import type { AiCompletionRequest, AiCompletionResult } from "../../types";

/**
 * Local / future LLM stub — echoes that local runtime is not wired yet.
 */
export class LocalLLMProvider implements AIProvider {
  readonly id = "local" as const;

  async complete(_req: AiCompletionRequest): Promise<AiCompletionResult> {
    return {
      success: false,
      content: "",
      provider: "local",
      model: "local-llm",
      message: "Local LLM provider is reserved for future use.",
    };
  }
}
