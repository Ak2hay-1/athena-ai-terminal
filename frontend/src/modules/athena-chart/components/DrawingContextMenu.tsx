"use client";

import type { ChartController } from "../engine/controller";
import { useDrawingStore } from "../store/drawing-store";

interface Props {
  engineRef: React.MutableRefObject<ChartController | null>;
}

export function DrawingContextMenu({ engineRef }: Props) {
  const menu = useDrawingStore((s) => s.contextMenu);
  const setContextMenu = useDrawingStore((s) => s.setContextMenu);
  if (!menu) return null;

  const mgr = engineRef.current?.drawingEngine.manager;
  const close = () => setContextMenu(null);

  const run = (fn: () => void) => {
    fn();
    close();
  };

  return (
    <>
      <div className="fixed inset-0 z-40" onClick={close} onContextMenu={(e) => e.preventDefault()} />
      <div
        className="fixed z-50 min-w-[160px] rounded-sm border border-border bg-panel-elevated py-1 text-[11px] shadow-xl"
        style={{ left: menu.x, top: menu.y }}
      >
        {[
          { label: "Delete", action: () => mgr?.remove(mgr.getSelected().map((o) => o.id)) },
          { label: "Duplicate", action: () => mgr?.duplicateSelected() },
          { label: "Copy", action: () => mgr?.copySelected() },
          { label: "Paste", action: () => mgr?.paste() },
          { label: "Bring Forward", action: () => mgr?.bringForward() },
          { label: "Send Backward", action: () => mgr?.sendBackward() },
          { label: "Lock", action: () => mgr?.setLocked(true) },
          { label: "Hide", action: () => mgr?.setVisible(false) },
          {
            label: "Change Color",
            action: () => mgr?.setColor("#ff6b00"),
          },
        ].map((item) => (
          <button
            key={item.label}
            type="button"
            className="block w-full px-3 py-1.5 text-left text-foreground hover:bg-panel"
            onClick={() => run(item.action)}
          >
            {item.label}
          </button>
        ))}
      </div>
    </>
  );
}
