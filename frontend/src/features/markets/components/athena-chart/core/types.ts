export type {
  ChartLevels,
  ChartMarker,
  PaneLayout,
  ViewportState,
  CrosshairState,
  EngineOptions,
} from "@/modules/athena-chart/types";

export {
  niceTicks,
  formatPriceLabel,
  formatTimeLabel,
} from "@/modules/athena-chart/utils/format";

import { candleTimeSec as timeSec } from "@/modules/athena-chart/utils/format";

/** Legacy helper — accepts candle-like objects. */
export function candleTimeSec(c: { time: string } | string): number {
  return typeof c === "string" ? timeSec(c) : timeSec(c.time);
}
