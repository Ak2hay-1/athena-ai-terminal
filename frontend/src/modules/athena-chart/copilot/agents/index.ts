import type { AthenaStructuredContext, PromptPacket } from "../types";
import {
  promptForCoach,
  promptForQuickAction,
  promptForSummary,
  promptForTradeReview,
  promptForClickExplain,
  buildPromptPacket,
} from "../prompts/builder";
import type { QuickActionId, SummaryHorizon } from "../types";

/** Thin agent wrappers — each builds a grounded prompt packet. */
export const CopilotAgents = {
  qa(ctx: AthenaStructuredContext, question: string): PromptPacket {
    return buildPromptPacket({ ctx, question });
  },
  quick(ctx: AthenaStructuredContext, action: QuickActionId): PromptPacket {
    return promptForQuickAction(ctx, action);
  },
  explainObject(ctx: AthenaStructuredContext): PromptPacket {
    return promptForClickExplain(ctx);
  },
  summary(ctx: AthenaStructuredContext, horizon: SummaryHorizon): PromptPacket {
    return promptForSummary(ctx, horizon);
  },
  coach(ctx: AthenaStructuredContext): PromptPacket {
    return promptForCoach(ctx);
  },
  review(ctx: AthenaStructuredContext): PromptPacket {
    return promptForTradeReview(ctx);
  },
};
