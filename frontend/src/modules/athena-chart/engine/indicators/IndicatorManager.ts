import type { Candlestick } from "../../types";
import type { IChartRenderer } from "../renderers/types";
import type { Viewport } from "../viewport";
import type { PaneLayout } from "../../types";
import { getIndicatorPlugin, listIndicatorPlugins } from "./registry";
import type { IndicatorInstance, IndicatorSettings } from "./types";
import { uid } from "../../utils/uid";

type CacheEntry = {
  key: string;
  values: unknown;
};

/**
 * Manages indicator instances, calculation cache, and render dispatch.
 */
export class IndicatorManager {
  private instances: IndicatorInstance[] = [];
  private cache = new Map<string, CacheEntry>();
  private favorites = new Set<string>();

  getInstances(): IndicatorInstance[] {
    return this.instances;
  }

  setInstances(instances: IndicatorInstance[]): void {
    this.instances = instances;
    this.cache.clear();
  }

  add(pluginId: string, settings?: Partial<IndicatorSettings>): IndicatorInstance | null {
    const plugin = getIndicatorPlugin(pluginId);
    if (!plugin) return null;
    const inst: IndicatorInstance = {
      instanceId: uid("ind-"),
      pluginId,
      settings: { ...plugin.meta.defaultSettings, ...settings },
      favorite: this.favorites.has(pluginId),
    };
    this.instances = [...this.instances, inst];
    return inst;
  }

  remove(instanceId: string): void {
    this.instances = this.instances.filter((i) => i.instanceId !== instanceId);
    this.cache.delete(instanceId);
  }

  duplicate(instanceId: string): void {
    const src = this.instances.find((i) => i.instanceId === instanceId);
    if (!src) return;
    this.instances = [
      ...this.instances,
      {
        ...src,
        instanceId: uid("ind-"),
        settings: { ...src.settings },
      },
    ];
  }

  updateSettings(instanceId: string, patch: Partial<IndicatorSettings>): void {
    this.instances = this.instances.map((i) =>
      i.instanceId === instanceId
        ? { ...i, settings: { ...i.settings, ...patch } }
        : i,
    );
    this.cache.delete(instanceId);
  }

  toggleFavorite(pluginId: string): void {
    if (this.favorites.has(pluginId)) this.favorites.delete(pluginId);
    else this.favorites.add(pluginId);
  }

  search(query: string) {
    const q = query.toLowerCase();
    return listIndicatorPlugins().filter(
      (p) =>
        p.meta.label.toLowerCase().includes(q) ||
        p.meta.id.toLowerCase().includes(q),
    );
  }

  private cacheKey(
    inst: IndicatorInstance,
    candles: Candlestick[],
  ): string {
    const last = candles[candles.length - 1]?.time ?? "";
    return `${inst.pluginId}:${inst.instanceId}:${JSON.stringify(inst.settings)}:${candles.length}:${last}`;
  }

  private getValues(inst: IndicatorInstance, candles: Candlestick[]): unknown {
    const key = this.cacheKey(inst, candles);
    const hit = this.cache.get(inst.instanceId);
    if (hit && hit.key === key) {
      if (typeof console !== "undefined" && process.env.NODE_ENV !== "production") {
        // eslint-disable-next-line no-console
        console.debug("[CACHE] INDICATOR CACHE HIT", inst.pluginId);
      }
      return hit.values;
    }
    const plugin = getIndicatorPlugin(inst.pluginId);
    if (!plugin) return null;
    const values = plugin.calculate({ candles, settings: inst.settings });
    this.cache.set(inst.instanceId, { key, values });
    return values;
  }

  renderAll(opts: {
    r: IChartRenderer;
    candles: Candlestick[];
    viewport: Viewport;
    layout: PaneLayout;
    priceY: (price: number, top: number, h: number) => number;
    start: number;
    end: number;
  }): void {
    const overlays = this.instances.filter((i) => {
      const p = getIndicatorPlugin(i.pluginId);
      return p?.meta.category === "overlay" && i.settings.visible;
    });
    const panes = this.instances.filter((i) => {
      const p = getIndicatorPlugin(i.pluginId);
      return p?.meta.category === "pane" && i.settings.visible;
    });

    for (const inst of overlays) {
      const plugin = getIndicatorPlugin(inst.pluginId);
      if (!plugin) continue;
      plugin.render({
        r: opts.r,
        viewport: opts.viewport,
        layout: opts.layout,
        priceY: opts.priceY,
        values: this.getValues(inst, opts.candles),
        settings: inst.settings,
        start: opts.start,
        end: opts.end,
      });
    }

    // Map pane plugins onto layout.panes by order
    panes.forEach((inst, idx) => {
      const plugin = getIndicatorPlugin(inst.pluginId);
      if (!plugin) return;
      const pane = opts.layout.panes[idx] ?? {
        id: inst.pluginId,
        top: opts.layout.rsiTop || opts.layout.macdTop,
        height: opts.layout.rsiH || opts.layout.macdH || 60,
      };
      plugin.render({
        r: opts.r,
        viewport: opts.viewport,
        layout: opts.layout,
        pane: { top: pane.top, height: pane.height },
        priceY: opts.priceY,
        values: this.getValues(inst, opts.candles),
        settings: inst.settings,
        start: opts.start,
        end: opts.end,
      });
    });
  }
}
