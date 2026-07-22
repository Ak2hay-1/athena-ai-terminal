"use client";

import { Bell, Newspaper, ShieldAlert, TrendingUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MARKET_SYMBOLS, TIMEFRAMES } from "@/constants/markets";
import {
  useDerivedAlerts,
  type AlertItem,
} from "@/features/alerts/hooks/use-derived-alerts";

function iconFor(kind: AlertItem["kind"]) {
  if (kind === "news") return Newspaper;
  if (kind === "signal") return TrendingUp;
  if (kind === "structure") return ShieldAlert;
  return Bell;
}

export function AlertsView() {
  const {
    alerts,
    highCount,
    symbolFilter,
    setSymbolFilter,
    timeframe,
    setSymbol,
    setTimeframe,
    isAll,
  } = useDerivedAlerts();

  return (
    <div className="mx-auto max-w-[1100px] space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Alerts
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            Intelligence alerts
          </h1>
          <p className="mt-1 text-sm text-muted">
            News impact, confidence shifts, and session context — not broker fills
            {isAll ? " · all pairs" : ` · ${symbolFilter}`}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="warning">{highCount} high</Badge>
          <select
            value={symbolFilter}
            onChange={(event) => {
              const next = event.target.value;
              setSymbolFilter(next);
              if (next !== "ALL") setSymbol(next);
            }}
            className="h-9 rounded-sm border border-border bg-panel px-3 font-mono text-sm outline-none focus:border-primary/50"
          >
            <option value="ALL">ALL</option>
            {MARKET_SYMBOLS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select
            value={timeframe}
            onChange={(event) => setTimeframe(event.target.value)}
            className="h-9 rounded-sm border border-border bg-panel px-3 font-mono text-sm outline-none focus:border-primary/50"
          >
            {TIMEFRAMES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>{alerts.length} active alerts</CardTitle>
          <Badge tone="bullish">Realtime poll</Badge>
        </CardHeader>
        <CardContent className="space-y-2">
          {alerts.map((alert) => {
            const Icon = iconFor(alert.kind);
            return (
              <div
                key={alert.id}
                className="flex gap-3 rounded-sm border border-border/70 bg-background/30 px-3 py-3"
              >
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border border-border bg-panel">
                  <Icon className="h-3.5 w-3.5 text-primary" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-medium">{alert.title}</p>
                    <div className="flex items-center gap-2">
                      <Badge
                        tone={
                          alert.severity === "high"
                            ? "warning"
                            : alert.severity === "medium"
                              ? "primary"
                              : "neutral"
                        }
                      >
                        {alert.severity}
                      </Badge>
                      <span className="text-[11px] text-muted">{alert.time}</span>
                    </div>
                  </div>
                  <p className="mt-1 text-xs text-muted">{alert.detail}</p>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
