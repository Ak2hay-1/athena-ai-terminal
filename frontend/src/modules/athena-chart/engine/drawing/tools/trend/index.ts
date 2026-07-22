import type { DrawingType } from "../../../../types";

export interface ToolDefinition {
  id: DrawingType;
  label: string;
  minPoints: number;
  maxPoints: number;
}

export const TOOL_TREND: ToolDefinition = {
  id: "trend",
  label: "Trend Line",
  minPoints: 2,
  maxPoints: 2,
};
