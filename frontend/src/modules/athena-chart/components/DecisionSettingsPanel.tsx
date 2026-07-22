"use client";

import { useDecisionStore } from "../decision-engine/store/decision-store";
import type { DecisionOverlayVisibility, SignalWeights } from "../decision-engine/types";
import { STRATEGY_PROFILES } from "../decision-engine/strategies/profiles";
import { cn } from "@/lib/utils";

const OVERLAY_KEYS: Array<{ key: keyof DecisionOverlayVisibility; label: string }> = [
  { key: "buyZone", label: "Buy Zone" },
  { key: "sellZone", label: "Sell Zone" },
  { key: "entry", label: "Entry" },
  { key: "stopLoss", label: "Stop Loss" },
  { key: "takeProfits", label: "Take Profits" },
  { key: "probabilityBadge", label: "Probability" },
  { key: "confidenceBadge", label: "Confidence" },
  { key: "riskBadge", label: "Risk Badge" },
  { key: "gradeBadge", label: "Grade Badge" },
];

const WEIGHT_KEYS: Array<{ key: keyof SignalWeights; label: string }> = [
  { key: "trend", label: "Trend" },
  { key: "order_block", label: "Order Block" },
  { key: "liquidity", label: "Liquidity" },
  { key: "volume", label: "Volume" },
  { key: "fvg", label: "FVG" },
  { key: "pattern", label: "Pattern" },
  { key: "bos", label: "BOS" },
  { key: "choch", label: "CHOCH" },
];

export function DecisionSettingsPanel({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const settings = useDecisionStore((s) => s.settings);
  const setSettings = useDecisionStore((s) => s.setSettings);
  const setOverlay = useDecisionStore((s) => s.setOverlay);
  const setWeight = useDecisionStore((s) => s.setWeight);

  if (!open) return null;

  return (
    <div className="absolute right-4 top-[22rem] z-40 max-h-[42vh] w-80 overflow-y-auto rounded-sm border border-border bg-panel-elevated p-3 shadow-xl">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
          Decision Engine
        </span>
        <button type="button" className="text-[11px] text-muted" onClick={onClose}>
          Close
        </button>
      </div>

      <label className="mb-2 flex items-center justify-between text-[11px]">
        Strategy
        <select
          value={settings.strategy}
          onChange={(e) =>
            setSettings({
              strategy: e.target.value as typeof settings.strategy,
            })
          }
          className="rounded-sm border border-border bg-panel px-1 text-[11px]"
        >
          {Object.values(STRATEGY_PROFILES).map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
      </label>

      <label className="mb-2 flex items-center justify-between text-[11px]">
        Risk mode
        <select
          value={settings.riskMode}
          onChange={(e) =>
            setSettings({
              riskMode: e.target.value as typeof settings.riskMode,
            })
          }
          className="rounded-sm border border-border bg-panel px-1 text-[11px]"
        >
          <option value="conservative">Conservative</option>
          <option value="balanced">Balanced</option>
          <option value="aggressive">Aggressive</option>
        </select>
      </label>

      <label className="mb-2 flex items-center justify-between text-[11px]">
        Entry style
        <select
          value={settings.entryStyle}
          onChange={(e) =>
            setSettings({
              entryStyle: e.target.value as typeof settings.entryStyle,
            })
          }
          className="rounded-sm border border-border bg-panel px-1 text-[11px]"
        >
          <option value="conservative">Conservative</option>
          <option value="balanced">Balanced</option>
          <option value="aggressive">Aggressive</option>
        </select>
      </label>

      <label className="mb-2 flex items-center justify-between text-[11px]">
        Min confidence
        <input
          type="number"
          min={0}
          max={100}
          value={settings.minConfidence}
          onChange={(e) =>
            setSettings({ minConfidence: Number(e.target.value) || 55 })
          }
          className="w-14 rounded-sm border border-border bg-panel px-1 font-mono"
        />
      </label>

      <label className="mb-3 flex items-center justify-between text-[11px]">
        Min RR
        <input
          type="number"
          min={0.5}
          max={10}
          step={0.1}
          value={settings.minRiskReward}
          onChange={(e) =>
            setSettings({ minRiskReward: Number(e.target.value) || 1.5 })
          }
          className="w-14 rounded-sm border border-border bg-panel px-1 font-mono"
        />
      </label>

      <div className="mb-1 text-[9px] uppercase tracking-wide text-muted-foreground">
        Signal weights
      </div>
      <div className="mb-3 space-y-1">
        {WEIGHT_KEYS.map(({ key, label }) => (
          <label key={key} className="flex items-center justify-between text-[10px]">
            <span>{label}</span>
            <input
              type="number"
              min={0}
              max={40}
              value={settings.signalWeights[key]}
              onChange={(e) => setWeight(key, Number(e.target.value) || 0)}
              className="w-12 rounded-sm border border-border bg-panel px-1 font-mono"
            />
          </label>
        ))}
      </div>

      <div className="mb-1 text-[9px] uppercase tracking-wide text-muted-foreground">
        Decision overlays
      </div>
      <div className="grid grid-cols-2 gap-1">
        {OVERLAY_KEYS.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setOverlay(key, !settings.overlays[key])}
            className={cn(
              "rounded-sm border px-1.5 py-1 text-left text-[10px]",
              settings.overlays[key]
                ? "border-primary/40 bg-primary/10 text-primary"
                : "border-border text-muted",
            )}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
