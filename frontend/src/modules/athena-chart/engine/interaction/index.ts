/**
 * Interaction helpers — pan/zoom math is owned by ChartController + Viewport.
 * Tool catalog for the terminal UI.
 */
import type { DrawingTool } from "../../types";

export const LEFT_TOOLS: Array<{ id: DrawingTool; label: string }> = [
  { id: "crosshair", label: "Crosshair" },
  { id: "cursor", label: "Cursor" },
  { id: "trend", label: "Trend Line" },
  { id: "hline", label: "Horizontal Line" },
  { id: "vline", label: "Vertical Line" },
  { id: "ray", label: "Ray" },
  { id: "rect", label: "Rectangle" },
  { id: "circle", label: "Circle" },
  { id: "text", label: "Text" },
  { id: "arrow", label: "Arrow" },
  { id: "fib", label: "Fib Retracement" },
  { id: "measure", label: "Measure Tool" },
  { id: "erase", label: "Erase" },
  { id: "magnet", label: "Magnet" },
  { id: "zoom", label: "Zoom" },
  { id: "hand", label: "Hand Tool" },
];

export { CHART_SHORTCUTS } from "./shortcuts";
