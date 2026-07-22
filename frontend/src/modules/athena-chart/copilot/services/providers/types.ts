import type {
  AiCompletionRequest,
  AiCompletionResult,
  AiProviderId,
} from "../../types";

/**
 * Provider abstraction — Copilot depends only on this interface.
 * Azure / OpenAI talk to Athena backend; Mock stays fully local.
 */
export interface AIProvider {
  readonly id: AiProviderId;
  complete(req: AiCompletionRequest): Promise<AiCompletionResult>;
}
