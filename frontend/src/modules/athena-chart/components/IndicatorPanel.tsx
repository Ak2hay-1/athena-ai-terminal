"use client";

import { useIndicatorStore } from "../store/indicator-store";

export function IndicatorPanel() {
  const open = useIndicatorStore((s) => s.panelOpen);
  const setPanelOpen = useIndicatorStore((s) => s.setPanelOpen);
  const instances = useIndicatorStore((s) => s.instances);
  const removeInstance = useIndicatorStore((s) => s.removeInstance);
  const duplicateInstance = useIndicatorStore((s) => s.duplicateInstance);
  const updateInstance = useIndicatorStore((s) => s.updateInstance);

  if (!open) return null;

  return (
    <div className="absolute bottom-8 left-12 z-30 w-72 rounded-sm border border-border bg-panel-elevated p-3 shadow-xl">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
          Indicator Manager
        </span>
        <button
          type="button"
          onClick={() => setPanelOpen(false)}
          className="text-[11px] text-muted hover:text-foreground"
        >
          Close
        </button>
      </div>
      <div className="max-h-64 space-y-2 overflow-y-auto">
        {instances.map((inst) => (
          <div
            key={inst.instanceId}
            className="rounded-sm border border-border-subtle bg-panel p-2"
          >
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-mono text-foreground">
                {inst.pluginId} · {inst.settings.length}
              </span>
              <div className="flex gap-1">
                <button
                  type="button"
                  className="text-[9px] text-muted hover:text-foreground"
                  onClick={() => duplicateInstance(inst.instanceId)}
                >
                  Dup
                </button>
                <button
                  type="button"
                  className="text-[9px] text-bearish"
                  onClick={() => removeInstance(inst.instanceId)}
                >
                  Del
                </button>
              </div>
            </div>
            <div className="mt-1 flex gap-2">
              <label className="flex items-center gap-1 text-[10px] text-muted">
                Len
                <input
                  type="number"
                  value={inst.settings.length}
                  onChange={(e) =>
                    updateInstance(inst.instanceId, {
                      length: Number(e.target.value) || 1,
                    })
                  }
                  className="w-12 rounded-sm border border-border bg-background px-1 py-0.5 font-mono"
                />
              </label>
              <label className="flex items-center gap-1 text-[10px] text-muted">
                Color
                <input
                  type="color"
                  value={inst.settings.color}
                  onChange={(e) =>
                    updateInstance(inst.instanceId, { color: e.target.value })
                  }
                  className="h-5 w-8 cursor-pointer border-0 bg-transparent"
                />
              </label>
              <label className="flex items-center gap-1 text-[10px] text-muted">
                <input
                  type="checkbox"
                  checked={inst.settings.visible}
                  onChange={(e) =>
                    updateInstance(inst.instanceId, {
                      visible: e.target.checked,
                    })
                  }
                />
                Vis
              </label>
            </div>
          </div>
        ))}
        {!instances.length ? (
          <p className="text-[11px] text-muted">No indicators. Add from menu.</p>
        ) : null}
      </div>
    </div>
  );
}
