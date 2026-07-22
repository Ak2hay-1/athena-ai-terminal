"use client";

import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchMarketSummary } from "@/services/ai";
import { useAuthStore } from "@/store/auth-store";

type Props = {
  symbol: string;
  timeframe: string;
  compact?: boolean;
};

export function MarketSummary({ symbol, timeframe, compact = false }: Props) {
  const user = useAuthStore((s) => s.user);
  const query = useQuery({
    queryKey: ["ai", "market-summary", symbol, timeframe],
    queryFn: () => fetchMarketSummary({ symbol, timeframe }),
    enabled: Boolean(user && symbol && timeframe),
    staleTime: 60_000,
  });

  if (query.isLoading) {
    return (
      <Card>
        <CardContent className="py-4 text-sm text-muted">
          Loading market summary…
        </CardContent>
      </Card>
    );
  }

  if (!query.data?.success) {
    return null;
  }

  const { summary, bullets, bias, cached } = query.data;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
        <CardTitle className="text-base">Market summary</CardTitle>
        <div className="flex items-center gap-2">
          {bias ? <Badge tone="ai">{bias}</Badge> : null}
          {cached ? <Badge tone="neutral">cached</Badge> : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-sm text-zinc-200">{summary}</p>
        {!compact && bullets.length > 0 ? (
          <ul className="list-disc space-y-1 pl-4 text-sm text-muted">
            {bullets.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}
      </CardContent>
    </Card>
  );
}
