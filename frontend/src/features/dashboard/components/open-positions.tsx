import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { priceDigitsFor } from "@/constants/markets";
import { formatPrice } from "@/lib/utils";
import type { Position } from "@/types";

export function OpenPositions({ positions }: { positions: Position[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Open Positions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {positions.length === 0 ? (
          <p className="text-sm text-muted">No open paper positions.</p>
        ) : (
          positions.map((position) => (
            <div
              key={position.id}
              className="flex items-center justify-between rounded-lg border border-border/70 bg-background/30 px-3 py-2.5"
            >
              <div>
                <p className="text-sm font-medium">
                  {position.symbol}{" "}
                  <span
                    className={
                      position.side === "BUY" ? "text-bullish" : "text-bearish"
                    }
                  >
                    {position.side}
                  </span>
                </p>
                <p className="text-xs text-muted">
                  Entry{" "}
                  {formatPrice(
                    position.entry,
                    priceDigitsFor(position.symbol, position.entry),
                  )}{" "}
                  · Vol {position.volume}
                </p>
              </div>
              <p
                className={`text-sm font-semibold tabular-nums ${
                  position.pnl >= 0 ? "text-bullish" : "text-bearish"
                }`}
              >
                {position.pnl >= 0 ? "+" : ""}
                {position.pnl.toFixed(1)}
              </p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
