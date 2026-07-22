import type { IndicatorPlugin } from "./types";
import { emaPlugin } from "./plugins/ema";
import { smaPlugin } from "./plugins/sma";
import { vwapPlugin } from "./plugins/vwap";
import { volumePlugin } from "./plugins/volume";
import { rsiPlugin } from "./plugins/rsi";
import { macdPlugin } from "./plugins/macd";
import { atrPlugin } from "./plugins/atr";
import { bollingerPlugin } from "./plugins/bollinger";

const REGISTRY = new Map<string, IndicatorPlugin>();

function register(p: IndicatorPlugin): void {
  REGISTRY.set(p.meta.id, p);
}

register(emaPlugin);
register(smaPlugin);
register(vwapPlugin);
register(volumePlugin);
register(rsiPlugin);
register(macdPlugin);
register(atrPlugin);
register(bollingerPlugin);

export function getIndicatorPlugin(id: string): IndicatorPlugin | undefined {
  return REGISTRY.get(id);
}

export function listIndicatorPlugins(): IndicatorPlugin[] {
  return [...REGISTRY.values()];
}
