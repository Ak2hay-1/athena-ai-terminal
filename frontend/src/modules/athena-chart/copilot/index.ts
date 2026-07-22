export type {
  AthenaStructuredContext,
  CopilotSettings,
  CopilotMessage,
  AiProviderId,
  ExplainTarget,
} from "./types";
export { DEFAULT_COPILOT_SETTINGS } from "./types";
export { buildAthenaContext } from "./context/builder";
export { buildPromptPacket } from "./prompts/builder";
export { getAIProvider, completeWithFallback } from "./services/providers/factory";
export { getCopilotService, CopilotService } from "./services/CopilotService";
export { useCopilotStore } from "./store/copilot-store";
export { useCopilot } from "./services/useCopilot";
export { CopilotPanel } from "./ui/CopilotPanel";
export { normalizeUserInput } from "./ui/inputLayer";
