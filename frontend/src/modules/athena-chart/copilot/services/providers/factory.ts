import type { AiProviderId } from "../../types";
import type { AIProvider } from "./types";
import { AzureOpenAIProvider } from "./azure";
import { OpenAIProvider } from "./openai";
import { LocalLLMProvider } from "./local";
import { MockProvider } from "./mock";

const cache = new Map<AiProviderId, AIProvider>();

export function getAIProvider(id: AiProviderId): AIProvider {
  const existing = cache.get(id);
  if (existing) return existing;
  let provider: AIProvider;
  switch (id) {
    case "openai":
      provider = new OpenAIProvider();
      break;
    case "local":
      provider = new LocalLLMProvider();
      break;
    case "mock":
      provider = new MockProvider();
      break;
    case "azure":
    default:
      provider = new AzureOpenAIProvider();
      break;
  }
  cache.set(id, provider);
  return provider;
}

/** Prefer primary; fall back to mock on hard failure. */
export async function completeWithFallback(
  primary: AiProviderId,
  req: Parameters<AIProvider["complete"]>[0],
) {
  const result = await getAIProvider(primary).complete(req);
  if (result.success && result.content.trim()) return result;
  if (primary === "mock") return result;
  return getAIProvider("mock").complete(req);
}
