"use client";

import { useIntelligenceStore } from "../intelligence/store/intelligence-store";
import type { OverlayVisibility } from "../intelligence/types";
import { cn } from "@/lib/utils";

const OVERLAY_KEYS: Array<{ key: keyof OverlayVisibility; label: string }> = [
  { key: "structure", label: "Structure" },
  { key: "swings", label: "Swings" },
  { key: "orderBlocks", label: "Order Blocks" },
  { key: "fvg", label: "FVG" },
  { key: "supplyDemand", label: "S/D Zones" },
  { key: "liquidity", label: "Liquidity" },
  { key: "supportResistance", label: "S/R" },
  { key: "trend", label: "Trend" },
  { key: "premiumDiscount", label: "Premium/Discount" },
  { key: "patterns", label: "Patterns" },
];

export function IntelligenceSettingsPanel({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const settings = useIntelligenceStore((s) => s.settings);
  const setSettings = useIntelligenceStore((s) => s.setSettings);
  const setOverlay = useIntelligenceStore((s) => s.setOverlay);

  if (!open) return null;

  return (
    <div className="absolute right-4 top-12 z-40 w-80 rounded-sm border border-border bg-panel-elevated p-3 shadow-xl">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
          Intelligence Settings
        </span>
        <button type="button" className="text-[11px] text-muted" onClick={onClose}>
          Close
        </button>
      </div>

      <label className="mb-2 flex items-center justify-between text-[11px]">
        Swing length
        <input
          type="number"
          min={2}
          max={20}
          value={settings.swingLength}
          onChange={(e) => setSettings({ swingLength: Number(e.target.value) || 5 })}
          className="w-14 rounded-sm border border-border bg-panel px-1 font-mono"
        />
      </label>
      <label className="mb-2 flex items-center justify-between text-[11px]">
        Sensitivity
        <input
          type="range"
          min={0}
          max={100}
          value={Math.round(settings.sensitivity * 100)}
          onChange={(e) =>
            setSettings({ sensitivity: Number(e.target.value) / 100 })
          }
          className="w-28"
        />
      </label>
      <label className="mb-2 flex items-center justify-between text-[11px]">
        Confidence threshold
        <input
          type="number"
          min={0}
          max={100}
          value={settings.confidenceThreshold}
          onChange={(e) =>
            setSettings({ confidenceThreshold: Number(e.target.value) || 40 })
          }
          className="w-14 rounded-sm border border-border bg-panel px-1 font-mono"
        />
      </label>
      <label className="mb-2 flex items-center justify-between text-[11px]">
        Detection mode
        <select
          value={settings.detectionMode}
          onChange={(e) =>
            setSettings({
              detectionMode: e.target.value as typeof settings.detectionMode,
            })
          }
          className="rounded-sm border border-border bg-panel px-1 text-[11px]"
        >
          <option value="strict">Strict</option>
          <option value="balanced">Balanced</option>
          <option value="aggressive">Aggressive</option>
        </select>
      </label>
      <label className="mb-2 flex items-center justify-between text-[11px]">
        Performance
        <select
          value={settings.performanceMode}
          onChange={(e) =>
            setSettings({
              performanceMode: e.target.value as typeof settings.performanceMode,
            })
          }
          className="rounded-sm border border-border bg-panel px-1 text-[11px]"
        >
          <option value="full">Full</option>
          <option value="fast">Fast</option>
        </select>
      </label>
      <label className="mb-1 flex items-center gap-2 text-[11px]">
        <input
          type="checkbox"
          checked={settings.noiseFilter}
          onChange={(e) => setSettings({ noiseFilter: e.target.checked })}
        />
        Noise filter
      </label>
      <label className="mb-3 flex items-center gap-2 text-[11px]">
        <input
          type="checkbox"
          checked={settings.adaptiveMode}
          onChange={(e) => setSettings({ adaptiveMode: e.target.checked })}
        />
        Adaptive swing
      </label>

      <div className="mb-1 text-[9px] uppercase tracking-wide text-muted-foreground">
        Overlay visibility
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
