"use client";

import { Radio } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { relativeTime } from "@/lib/mappers";
import { cn } from "@/lib/utils";
import type { NewsContext, NewsHeadline } from "@/types";

function sentimentTone(
  sentiment?: string,
): "bullish" | "bearish" | "neutral" | "warning" {
  const raw = String(sentiment ?? "").toUpperCase();
  if (raw.includes("BULL")) return "bullish";
  if (raw.includes("BEAR")) return "bearish";
  if (raw.includes("HIGH")) return "warning";
  return "neutral";
}

export function HighImpactNews({
  items,
  context,
  calendar = [],
  refreshing = false,
}: {
  items: NewsHeadline[];
  context?: NewsContext;
  calendar?: NewsHeadline[];
  refreshing?: boolean;
}) {
  const highImpact = items.filter((item) => item.impact === "High");
  const feed = (highImpact.length > 0 ? highImpact : items).slice(0, 6);
  const upcoming = (context?.upcomingEvents ?? [])
    .slice(0, 3)
    .map((event, index) => ({
      id: `upcoming-${index}`,
      title: event.title,
      impact: event.impact,
      time: event.publishedAt ? relativeTime(event.publishedAt) : "soon",
      symbols: [] as string[],
    }));
  const calendarPreview = upcoming.length > 0 ? upcoming : calendar.slice(0, 3);

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
        <div>
          <div className="flex items-center gap-2">
            <CardTitle>News & Calendar</CardTitle>
            <Badge tone={refreshing ? "warning" : "bullish"}>
              <Radio className={cn("mr-1 h-3 w-3", refreshing && "animate-pulse")} />
              {refreshing ? "Syncing" : "Live"}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-muted">
            Polls every 30s · high-impact windows affect risk
          </p>
        </div>
        {context ? (
          <Badge tone={sentimentTone(context.sentiment)}>
            {context.sentiment}
            {context.score !== 0 ? ` · ${context.score > 0 ? "+" : ""}${context.score}` : ""}
          </Badge>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-4">
        {context?.highImpactUpcoming ? (
          <div className="rounded-sm border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-warning">
            High-impact news window approaching
            {context.upcomingEvents?.[0]
              ? ` — ${context.upcomingEvents[0].title}`
              : "."}
          </div>
        ) : null}

        {context?.headlines && context.headlines.length > 0 ? (
          <div className="space-y-1.5">
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
              Context
            </p>
            <ul className="space-y-1">
              {context.headlines.slice(0, 3).map((headline) => (
                <li key={headline} className="text-xs leading-snug text-zinc-300">
                  · {headline}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="space-y-2.5">
          <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
            Latest
          </p>
          {feed.length === 0 ? (
            <p className="text-sm text-muted">No news events loaded.</p>
          ) : (
            feed.map((item) => (
              <div
                key={item.id}
                className="rounded-sm border border-border/70 bg-background/30 px-3 py-2.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <Badge tone={item.impact === "High" ? "warning" : "default"}>
                    {item.impact}
                  </Badge>
                  <span className="text-[11px] text-muted-foreground">{item.time}</span>
                </div>
                <p className="mt-2 text-sm leading-snug text-zinc-200">{item.title}</p>
                {item.summary ? (
                  <p className="mt-1 line-clamp-2 text-[11px] text-muted">{item.summary}</p>
                ) : null}
                <p className="mt-1 text-[11px] text-muted">
                  {item.symbols.join(" · ") || "Market"}
                </p>
              </div>
            ))
          )}
        </div>

        {calendarPreview.length > 0 ? (
          <div className="space-y-2 border-t border-border pt-3">
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
              Calendar
            </p>
            {calendarPreview.map((item) => (
              <div
                key={item.id}
                className="flex items-start justify-between gap-3 text-xs"
              >
                <div className="min-w-0">
                  <p className="truncate text-zinc-200">{item.title}</p>
                  <p className="text-muted">{item.time}</p>
                </div>
                <Badge tone={item.impact === "High" ? "warning" : "default"}>
                  {item.impact}
                </Badge>
              </div>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
