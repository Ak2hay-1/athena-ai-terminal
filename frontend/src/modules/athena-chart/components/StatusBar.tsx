"use client";

import { useChartStore } from "../store/chart-store";
import { useChartUiStore } from "../store/ui-store";
import { useDrawingStore } from "../store/drawing-store";
import { formatPriceLabel } from "../utils/format";

export function StatusBar() {
  const symbol = useChartStore((s) => s.symbol);
  const timeframe = useChartStore((s) => s.timeframe);
  const candleCount = useChartStore((s) => s.candleCount);
  const fps = useChartUiStore((s) => s.fps);
  const hoverPrice = useChartUiStore((s) => s.hoverPrice);
  const magnetMode = useDrawingStore((s) => s.magnetMode);
  const canUndo = useDrawingStore((s) => s.canUndo);
  const canRedo = useDrawingStore((s) => s.canRedo);
  const tool = useDrawingStore((s) => s.tool);

  return (
    <footer className="flex h-6 shrink-0 items-center gap-3 border-t border-border bg-[#050505] px-3 font-mono text-[10px] text-muted-foreground">
      <span className="text-primary">{symbol}</span>
      <span>{timeframe}</span>
      <span>{candleCount} bars</span>
      <span>Tool {tool}</span>
      <span>Magnet {magnetMode}</span>
      <span>
        Cursor {hoverPrice != null ? formatPriceLabel(hoverPrice) : "—"}
      </span>
      <span className={canUndo ? "text-foreground" : ""}>Undo{canUndo ? "*" : ""}</span>
      <span className={canRedo ? "text-foreground" : ""}>Redo{canRedo ? "*" : ""}</span>
      <span className="ml-auto">{fps} FPS</span>
    </footer>
  );
}
