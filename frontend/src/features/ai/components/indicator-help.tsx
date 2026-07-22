"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { explainIndicator } from "@/services/ai";
import { useAuthStore } from "@/store/auth-store";

const TOPICS = [
  { value: "fvg", label: "FVG" },
  { value: "order_block", label: "Order block" },
  { value: "liquidity", label: "Liquidity" },
  { value: "market_structure", label: "Structure" },
  { value: "momentum", label: "Momentum" },
  { value: "rsi", label: "RSI" },
  { value: "atr", label: "ATR" },
  { value: "confluence", label: "Confluence" },
];

type Props = {
  symbol: string;
  timeframe: string;
};

export function IndicatorHelp({ symbol, timeframe }: Props) {
  const user = useAuthStore((s) => s.user);
  const [open, setOpen] = useState(false);
  const [topic, setTopic] = useState("fvg");

  const query = useQuery({
    queryKey: ["ai", "indicator", topic, symbol, timeframe],
    queryFn: () => explainIndicator({ topic, symbol, timeframe }),
    enabled: Boolean(user && open && topic),
  });

  return (
    <div className="relative">
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => setOpen((v) => !v)}
      >
        <HelpCircle className="h-3.5 w-3.5" />
        Indicator help
      </Button>

      {open ? (
        <Card className="absolute right-0 z-20 mt-2 w-[min(420px,calc(100vw-2rem))] shadow-lg">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Indicator help</CardTitle>
            <p className="text-xs text-muted">
              Educational only — grounded in Athena context when available.
            </p>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-1.5">
              {TOPICS.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  onClick={() => setTopic(item.value)}
                  className={
                    topic === item.value
                      ? "rounded-sm border border-ai/40 bg-ai/10 px-2 py-1 text-[11px] text-ai"
                      : "rounded-sm border border-border px-2 py-1 text-[11px] text-muted hover:text-foreground"
                  }
                >
                  {item.label}
                </button>
              ))}
            </div>

            {query.isFetching ? (
              <p className="text-sm text-muted">Loading…</p>
            ) : query.data?.success ? (
              <div className="space-y-2 text-sm">
                <p className="text-zinc-200">{query.data.summary}</p>
                {query.data.athena_usage ? (
                  <p className="text-muted">
                    <span className="text-foreground">Athena usage: </span>
                    {query.data.athena_usage}
                  </p>
                ) : null}
                {query.data.how_it_works.length > 0 ? (
                  <ul className="list-disc space-y-1 pl-4 text-muted">
                    {query.data.how_it_works.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : (
              <p className="text-sm text-muted">
                {query.data?.message ?? "Select a topic to learn more."}
              </p>
            )}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
