import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ActivityEvent } from "@/types";
import { cn } from "@/lib/utils";

const toneDot: Record<ActivityEvent["tone"], string> = {
  ai: "bg-ai",
  market: "bg-primary",
  system: "bg-muted-foreground",
  trade: "bg-bullish",
};

export function ActivityTimeline({ events }: { events: ActivityEvent[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Activity Timeline</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {events.map((event, index) => (
          <div key={event.id} className="relative flex gap-3">
            {index < events.length - 1 ? (
              <span className="absolute top-3 left-[5px] h-[calc(100%+8px)] w-px bg-border" />
            ) : null}
            <span
              className={cn(
                "relative z-10 mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full",
                toneDot[event.tone],
              )}
            />
            <div className="min-w-0 flex-1">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium">{event.title}</p>
                <span className="shrink-0 text-[11px] text-muted-foreground">
                  {event.time}
                </span>
              </div>
              <p className="text-xs text-muted">{event.description}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
