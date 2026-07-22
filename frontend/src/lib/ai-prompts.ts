import { symbolCategory } from "@/constants/markets";
import type { Signal } from "@/types";

export function getSuggestedPrompts(
  symbol: string,
  timeframe: string,
  signal?: Signal | null,
): string[] {
  const cat = symbolCategory(symbol);
  const assetLabel = cat === "metals" ? "metals" : "FX";

  const whyPrompt =
    signal === "NO_TRADE"
      ? `Why no trade on ${symbol}?`
      : signal === "HOLD" || signal === "NEUTRAL"
        ? `Why standby on ${symbol}?`
        : signal
          ? `Why ${signal.replace("_", " ")} on ${symbol}?`
          : `Why this signal on ${symbol}?`;

  return [
    `Analyze ${symbol} ${timeframe} setup`,
    whyPrompt,
    `News risk for ${symbol}`,
    `Risk plan (SL/TP) for ${symbol}`,
    `Explain ${assetLabel} session bias for ${symbol}`,
  ];
}
