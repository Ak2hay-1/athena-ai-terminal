import type { PaneLayout } from "../../types";
import { BOTTOM_AXIS, PAD_TOP, RIGHT_AXIS } from "../layers/context";

export function computeLayout(
  width: number,
  height: number,
  mode: "advanced" | "overview",
  indicators: { rsi: boolean; macd: boolean },
  rsiFrac: number,
  macdFrac: number,
): PaneLayout {
  const interactive = mode === "advanced";
  const showRsi = interactive && indicators.rsi;
  const showMacd = interactive && indicators.macd;
  const plotRight = width - RIGHT_AXIS;
  const plotBottom = height - BOTTOM_AXIS;
  let mainBottom = plotBottom;
  let rsiTop = 0;
  let rsiH = 0;
  let macdTop = 0;
  let macdH = 0;
  const available = plotBottom - PAD_TOP;
  if (showRsi && showMacd) {
    rsiH = available * rsiFrac;
    macdH = available * macdFrac;
    mainBottom = plotBottom - rsiH - macdH;
    rsiTop = mainBottom;
    macdTop = mainBottom + rsiH;
  } else if (showRsi) {
    rsiH = available * rsiFrac;
    mainBottom = plotBottom - rsiH;
    rsiTop = mainBottom;
  } else if (showMacd) {
    macdH = available * macdFrac;
    mainBottom = plotBottom - macdH;
    macdTop = mainBottom;
  }
  return {
    plotLeft: 0,
    plotWidth: Math.max(1, plotRight),
    mainTop: PAD_TOP,
    mainH: Math.max(40, mainBottom - PAD_TOP),
    rsiTop,
    rsiH,
    macdTop,
    macdH,
    showRsi,
    showMacd,
    plotBottom,
    panes: [
      ...(showRsi ? [{ id: "rsi", top: rsiTop, height: rsiH }] : []),
      ...(showMacd ? [{ id: "macd", top: macdTop, height: macdH }] : []),
    ],
  };
}
