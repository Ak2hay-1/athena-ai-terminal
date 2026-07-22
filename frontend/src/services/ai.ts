import { apiFetch } from "@/services/api-client";

export type AiChatRole = "user" | "assistant" | "system";

export type AiChatMessage = {
  role: AiChatRole;
  content: string;
};

export type AiChatResult = {
  success: boolean;
  reply: string;
  provider?: string | null;
  model?: string | null;
  message?: string | null;
  redirected?: boolean;
};

export type ExplanationSections = {
  trend?: string;
  momentum?: string;
  structure?: string;
  liquidity?: string;
  risk?: string;
  entry_sl_tp?: string;
  confidence?: string;
  probability?: string;
  quality?: string;
};

export type TradeExplanationResult = {
  success: boolean;
  reasons: string[];
  sections?: ExplanationSections | null;
  provider?: string | null;
  model?: string | null;
  cached?: boolean;
  message?: string | null;
};

export type MarketSummaryResult = {
  success: boolean;
  summary: string;
  bullets: string[];
  bias?: string | null;
  sections?: Record<string, string> | null;
  provider?: string | null;
  model?: string | null;
  cached?: boolean;
  message?: string | null;
};

export type IndicatorExplanationResult = {
  success: boolean;
  topic: string;
  summary: string;
  how_it_works: string[];
  athena_usage: string;
  pitfalls: string[];
  provider?: string | null;
  model?: string | null;
  cached?: boolean;
  message?: string | null;
};

export type StrategyLessonResult = {
  success: boolean;
  topic: string;
  title: string;
  lesson: string;
  key_points: string[];
  exercise: string;
  common_mistakes: string[];
  provider?: string | null;
  model?: string | null;
  cached?: boolean;
  message?: string | null;
};

export type SessionSummaryResult = {
  success: boolean;
  summary: string;
  highlights: string[];
  risk_notes: string[];
  lessons: string[];
  provider?: string | null;
  model?: string | null;
  cached?: boolean;
  message?: string | null;
};

type Envelope<T> = {
  success: boolean;
  data?: T | null;
  message?: string | null;
};

export async function chatWithAthena(input: {
  messages: AiChatMessage[];
  symbol?: string;
  timeframe?: string;
}): Promise<AiChatResult> {
  const response = await apiFetch<Envelope<{
    reply?: string;
    provider?: string | null;
    model?: string | null;
    success?: boolean;
    message?: string | null;
    redirected?: boolean;
  }>>("/ai/chat", {
    method: "POST",
    body: JSON.stringify({
      messages: input.messages,
      symbol: input.symbol,
      timeframe: input.timeframe,
    }),
  });

  const reply = response.data?.reply?.trim() ?? "";
  const ok = Boolean(response.success && response.data?.success !== false && reply);

  return {
    success: ok,
    reply: reply || response.message || response.data?.message || "No reply from Athena.",
    provider: response.data?.provider,
    model: response.data?.model,
    message: response.message ?? response.data?.message,
    redirected: Boolean(response.data?.redirected),
  };
}

export async function explainTrade(input: {
  recommendationId?: number | string;
  symbol?: string;
  timeframe?: string;
  snapshot?: Record<string, unknown>;
}): Promise<TradeExplanationResult> {
  const response = await apiFetch<Envelope<{
    reasons?: string[];
    sections?: ExplanationSections | null;
    provider?: string | null;
    model?: string | null;
    cached?: boolean;
    success?: boolean;
    message?: string | null;
  }>>("/ai/explain-trade", {
    method: "POST",
    body: JSON.stringify({
      recommendation_id: input.recommendationId != null
        ? Number(input.recommendationId)
        : undefined,
      symbol: input.symbol,
      timeframe: input.timeframe,
      snapshot: input.snapshot,
    }),
  });

  return {
    success: Boolean(response.success && response.data?.success !== false),
    reasons: response.data?.reasons ?? [],
    sections: response.data?.sections,
    provider: response.data?.provider,
    model: response.data?.model,
    cached: response.data?.cached,
    message: response.message ?? response.data?.message,
  };
}

export async function fetchMarketSummary(input: {
  symbol: string;
  timeframe: string;
}): Promise<MarketSummaryResult> {
  const response = await apiFetch<Envelope<{
    summary?: string;
    bullets?: string[];
    bias?: string | null;
    sections?: Record<string, string> | null;
    provider?: string | null;
    model?: string | null;
    cached?: boolean;
    success?: boolean;
    message?: string | null;
  }>>("/ai/market-summary", {
    method: "POST",
    body: JSON.stringify(input),
  });

  return {
    success: Boolean(response.success && response.data?.success !== false),
    summary: response.data?.summary ?? "",
    bullets: response.data?.bullets ?? [],
    bias: response.data?.bias,
    sections: response.data?.sections,
    provider: response.data?.provider,
    model: response.data?.model,
    cached: response.data?.cached,
    message: response.message ?? response.data?.message,
  };
}

export async function explainIndicator(input: {
  topic: string;
  symbol?: string;
  timeframe?: string;
}): Promise<IndicatorExplanationResult> {
  const response = await apiFetch<Envelope<{
    topic?: string;
    summary?: string;
    how_it_works?: string[];
    athena_usage?: string;
    pitfalls?: string[];
    provider?: string | null;
    model?: string | null;
    cached?: boolean;
    success?: boolean;
    message?: string | null;
  }>>("/ai/explain-indicator", {
    method: "POST",
    body: JSON.stringify(input),
  });

  return {
    success: Boolean(response.success && response.data?.success !== false),
    topic: response.data?.topic ?? input.topic,
    summary: response.data?.summary ?? "",
    how_it_works: response.data?.how_it_works ?? [],
    athena_usage: response.data?.athena_usage ?? "",
    pitfalls: response.data?.pitfalls ?? [],
    provider: response.data?.provider,
    model: response.data?.model,
    cached: response.data?.cached,
    message: response.message ?? response.data?.message,
  };
}

export async function teachStrategy(topic: string): Promise<StrategyLessonResult> {
  const response = await apiFetch<Envelope<{
    topic?: string;
    title?: string;
    lesson?: string;
    key_points?: string[];
    exercise?: string;
    common_mistakes?: string[];
    provider?: string | null;
    model?: string | null;
    cached?: boolean;
    success?: boolean;
    message?: string | null;
  }>>("/ai/teach", {
    method: "POST",
    body: JSON.stringify({ topic }),
  });

  return {
    success: Boolean(response.success && response.data?.success !== false),
    topic: response.data?.topic ?? topic,
    title: response.data?.title ?? "",
    lesson: response.data?.lesson ?? "",
    key_points: response.data?.key_points ?? [],
    exercise: response.data?.exercise ?? "",
    common_mistakes: response.data?.common_mistakes ?? [],
    provider: response.data?.provider,
    model: response.data?.model,
    cached: response.data?.cached,
    message: response.message ?? response.data?.message,
  };
}

export async function summarizeSession(
  stats: Record<string, unknown>,
): Promise<SessionSummaryResult> {
  const response = await apiFetch<Envelope<{
    summary?: string;
    highlights?: string[];
    risk_notes?: string[];
    lessons?: string[];
    provider?: string | null;
    model?: string | null;
    cached?: boolean;
    success?: boolean;
    message?: string | null;
  }>>("/ai/session-summary", {
    method: "POST",
    body: JSON.stringify(stats),
  });

  return {
    success: Boolean(response.success && response.data?.success !== false),
    summary: response.data?.summary ?? "",
    highlights: response.data?.highlights ?? [],
    risk_notes: response.data?.risk_notes ?? [],
    lessons: response.data?.lessons ?? [],
    provider: response.data?.provider,
    model: response.data?.model,
    cached: response.data?.cached,
    message: response.message ?? response.data?.message,
  };
}
