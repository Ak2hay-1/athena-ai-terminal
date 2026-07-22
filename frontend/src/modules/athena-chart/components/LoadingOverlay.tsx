"use client";

export function LoadingOverlay({ visible }: { visible: boolean }) {
  if (!visible) return null;
  return (
    <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-black/40">
      <div className="rounded-sm border border-border bg-panel px-3 py-2 font-mono text-[11px] text-muted">
        Loading series…
      </div>
    </div>
  );
}
