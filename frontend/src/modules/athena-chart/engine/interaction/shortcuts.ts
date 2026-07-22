/**
 * Keyboard shortcut catalog (handled in ChartController.onKeyDown).
 * Documented here so UI can surface help without owning logic.
 */
export const CHART_SHORTCUTS = [
  { keys: "Delete", action: "Delete selected drawings" },
  { keys: "Ctrl+C", action: "Copy" },
  { keys: "Ctrl+V", action: "Paste" },
  { keys: "Ctrl+Z", action: "Undo" },
  { keys: "Ctrl+Y / Ctrl+Shift+Z", action: "Redo" },
  { keys: "Space", action: "Hand tool" },
  { keys: "Esc", action: "Cancel / deselect" },
  { keys: "T", action: "Trend line" },
  { keys: "H", action: "Horizontal line" },
  { keys: "R", action: "Rectangle" },
  { keys: "F", action: "Fibonacci" },
  { keys: "M", action: "Measure" },
  { keys: "V", action: "Vertical line" },
] as const;
