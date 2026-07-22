"use client";

import { useIntelligenceStore } from "../intelligence/store/intelligence-store";
import { useDecisionStore } from "../decision-engine/store/decision-store";
import { cn } from "@/lib/utils";

export function BottomTimeline() {
  const intelEvents = useIntelligenceStore((s) => s.events);
  const decisionEvents = useDecisionStore((s) => s.events);

  const events = [...intelEvents, ...decisionEvents]
    .sort((a, b) => a.timeSec - b.timeSec)
    .slice(-20);

  return (
    <div className="flex h-14 shrink-0 flex-col border-t border-border bg-[#080808]">
      <div className="flex items-center gap-3 border-b border-border-subtle px-3 py-1">
        <span className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
          Timeline
        </span>
        <span className="text-[9px] text-muted">AI + Decision events</span>
      </div>
      <div className="relative flex-1 overflow-x-auto overflow-y-hidden">
        <div className="absolute inset-x-0 top-1/2 h-px bg-border" />
        <div className="flex h-full min-w-max items-center gap-4 px-3">
          {events.map((e) => (
            <div key={e.id} className="relative flex flex-col items-center">
              <div
                className={cn(
                  "h-2 w-2 rounded-full",
                  e.bias === "bullish"
                    ? "bg-bullish"
                    : e.bias === "bearish"
                      ? "bg-bearish"
                      : "bg-primary",
                )}
              />
              <div className="mt-0.5 max-w-[72px] truncate text-center font-mono text-[8px] text-muted">
                {new Date(e.timeSec * 1000).toISOString().slice(11, 16)}
              </div>
              <div className="max-w-[80px] truncate text-center text-[8px] text-foreground">
                {e.label}
              </div>
            </div>
          ))}
          {!events.length ? (
            <span className="text-[10px] text-muted">No analysis events yet</span>
          ) : null}
        </div>
      </div>
    </div>
  );
}
