import { apiFetch } from "@/services/api-client";
import { formatImpact, relativeTime } from "@/lib/mappers";
import type { NewsContext, NewsHeadline } from "@/types";

interface NewsEventRaw {
  id: number | string;
  title: string;
  summary?: string | null;
  impact?: string;
  published_at?: string;
  symbols?: string[];
  sentiment_score?: number;
  source?: string | null;
}

interface NewsContextRaw {
  sentiment?: string;
  score?: number;
  confidence?: number;
  high_impact_upcoming?: boolean;
  headlines?: string[];
  reasons?: string[];
  upcoming_events?: Array<{
    title: string;
    impact: string;
    published_at: string;
  }>;
}

function mapHeadline(item: NewsEventRaw, fallbackSymbol?: string): NewsHeadline {
  return {
    id: String(item.id),
    title: item.title,
    summary: item.summary ?? undefined,
    impact: formatImpact(item.impact),
    time: item.published_at ? relativeTime(item.published_at) : "—",
    publishedAt: item.published_at,
    symbols: item.symbols ?? (fallbackSymbol ? [fallbackSymbol] : []),
    sentimentScore: item.sentiment_score,
    source: item.source ?? undefined,
  };
}

export async function getNewsContext(symbol: string): Promise<NewsContext> {
  const raw = await apiFetch<NewsContextRaw>(
    `/news/context?symbol=${encodeURIComponent(symbol)}`,
  );

  return {
    sentiment: raw.sentiment ?? "NEUTRAL",
    score: raw.score ?? 0,
    confidence: raw.confidence,
    highImpactUpcoming: Boolean(raw.high_impact_upcoming),
    headlines: raw.headlines ?? [],
    reasons: raw.reasons ?? [],
    upcomingEvents: (raw.upcoming_events ?? []).map((event) => ({
      title: event.title,
      impact: formatImpact(event.impact),
      publishedAt: event.published_at,
    })),
  };
}

export async function getLatestNews(
  symbol: string,
  limit = 8,
): Promise<NewsHeadline[]> {
  const raw = await apiFetch<NewsEventRaw[]>(
    `/news/latest?symbol=${encodeURIComponent(symbol)}&limit=${limit}`,
  );

  return raw.map((item) => mapHeadline(item, symbol));
}

export async function getCalendar(limit = 10): Promise<NewsHeadline[]> {
  const raw = await apiFetch<NewsEventRaw[]>(`/news/calendar?limit=${limit}`);
  return raw.map((item) => mapHeadline(item));
}
