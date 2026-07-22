"use client";

import {
  Crosshair,
  MousePointer2,
  Minus,
  MoveVertical,
  Square,
  Circle,
  Type,
  MoveUpRight,
  Spline,
  Ruler,
  Eraser,
  Magnet,
  ZoomIn,
  Hand,
  TrendingUp,
  ArrowUpRight,
} from "lucide-react";
import type { DrawingTool } from "../types";
import { useDrawingStore } from "../store/drawing-store";
import { ToolButton } from "./ToolButton";

const TOOLS: Array<{
  id: DrawingTool;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
  { id: "crosshair", label: "Crosshair", icon: Crosshair },
  { id: "cursor", label: "Select / Cursor", icon: MousePointer2 },
  { id: "trend", label: "Trend Line (T)", icon: TrendingUp },
  { id: "hline", label: "Horizontal Line (H)", icon: Minus },
  { id: "vline", label: "Vertical Line", icon: MoveVertical },
  { id: "ray", label: "Ray", icon: ArrowUpRight },
  { id: "rect", label: "Rectangle (R)", icon: Square },
  { id: "circle", label: "Circle / Ellipse", icon: Circle },
  { id: "text", label: "Text", icon: Type },
  { id: "arrow", label: "Arrow", icon: MoveUpRight },
  { id: "fib", label: "Fib Retracement (F)", icon: Spline },
  { id: "measure", label: "Measure (M)", icon: Ruler },
  { id: "erase", label: "Erase", icon: Eraser },
  { id: "magnet", label: "Magnet", icon: Magnet },
  { id: "zoom", label: "Zoom", icon: ZoomIn },
  { id: "hand", label: "Hand (Space)", icon: Hand },
];

export function LeftTools() {
  const tool = useDrawingStore((s) => s.tool);
  const magnetMode = useDrawingStore((s) => s.magnetMode);
  const setTool = useDrawingStore((s) => s.setTool);

  return (
    <aside className="flex w-10 shrink-0 flex-col items-center gap-0.5 overflow-y-auto border-r border-border bg-[#080808] py-2">
      {TOOLS.map(({ id, label, icon: Icon }) => {
        const active =
          id === "magnet" ? magnetMode !== "off" : tool === id;
        const magnetLabel =
          id === "magnet" ? `Magnet: ${magnetMode}` : label;
        return (
          <ToolButton
            key={id}
            label={magnetLabel}
            active={active}
            onClick={() => setTool(id)}
          >
            <Icon className="h-3.5 w-3.5" />
          </ToolButton>
        );
      })}
    </aside>
  );
}
