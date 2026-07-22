"use client";

import { useAlertStore, type AlertKind } from "../store/alert-store";
import { useChartStore } from "../store/chart-store";

const KINDS: AlertKind[] = ["price", "trendline", "indicator", "cross", "time"];

/** Alerts architecture UI — no backend. */
export function AlertsStubDialog() {
  const open = useAlertStore((s) => s.draftOpen);
  const setDraftOpen = useAlertStore((s) => s.setDraftOpen);
  const addAlert = useAlertStore((s) => s.addAlert);
  const alerts = useAlertStore((s) => s.alerts);
  const symbol = useChartStore((s) => s.symbol);

  if (!open) return null;

  return (
    <div className="absolute right-4 top-12 z-40 w-72 rounded-sm border border-border bg-panel-elevated p-3 shadow-xl">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
          Create Alert
        </span>
        <button type="button" className="text-[11px] text-muted" onClick={() => setDraftOpen(false)}>
          Close
        </button>
      </div>
      <div className="space-y-1">
        {KINDS.map((kind) => (
          <button
            key={kind}
            type="button"
            className="block w-full rounded-sm border border-border px-2 py-1.5 text-left text-[11px] capitalize hover:bg-panel"
            onClick={() => {
              addAlert({
                kind,
                symbol,
                label: `${kind} alert on ${symbol}`,
                payload: {},
              });
            }}
          >
            {kind} alert
          </button>
        ))}
      </div>
      <div className="mt-3 border-t border-border pt-2 text-[10px] text-muted">
        {alerts.length} alert(s) stored locally — firing not implemented.
      </div>
    </div>
  );
}
