/**
 * Cost gate — when GPT may be called.
 * Never on every candle.
 */

export type CopilotTrigger =
  | "user_open"
  | "user_question"
  | "quick_action"
  | "click_explain"
  | "decision_change"
  | "trade_close"
  | "major_news";

const ALLOWED: Set<CopilotTrigger> = new Set([
  "user_open",
  "user_question",
  "quick_action",
  "click_explain",
  "decision_change",
  "trade_close",
  "major_news",
]);

export function mayCallGpt(trigger: CopilotTrigger): boolean {
  return ALLOWED.has(trigger);
}

export function significantDecisionChange(
  prevConf: number | null,
  nextConf: number,
  minDelta: number,
): boolean {
  if (prevConf == null) return true;
  return Math.abs(nextConf - prevConf) >= minDelta;
}
