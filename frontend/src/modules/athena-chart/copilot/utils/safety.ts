import type { AthenaStructuredContext } from "../types";

const FORBIDDEN_PATTERNS = [
  /as an ai language model/i,
  /i made up/i,
  /assuming price is/i,
];

/**
 * Lightweight response guard — flags obvious invention patterns.
 * Does not rewrite GPT; callers may append a disclaimer.
 */
export function validateCopilotReply(
  reply: string,
  ctx: AthenaStructuredContext,
): { ok: boolean; warnings: string[] } {
  const warnings: string[] = [];
  if (!reply.trim()) {
    return { ok: false, warnings: ["Empty reply"] };
  }
  for (const p of FORBIDDEN_PATTERNS) {
    if (p.test(reply)) warnings.push(`Matched discouraged pattern: ${p}`);
  }
  if (ctx.dataGaps.length && /definitely|certainly|guaranteed/i.test(reply)) {
    warnings.push("High-certainty language while data gaps exist");
  }
  // If opportunity missing, warn if reply asserts a grade
  if (!ctx.opportunity && /\bgrade\s*A\+?/i.test(reply)) {
    warnings.push("Asserted trade grade without Decision Engine opportunity");
  }
  return { ok: warnings.length === 0, warnings };
}

export function appendSafetyFooter(
  reply: string,
  ctx: AthenaStructuredContext,
): string {
  if (!ctx.dataGaps.length) return reply;
  return `${reply.trim()}\n\n—\nNote: Athena reported missing data: ${ctx.dataGaps.join(", ")}.`;
}
