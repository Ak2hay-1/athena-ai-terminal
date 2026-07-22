"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import { TooltipProvider } from "@/components/ui/tooltip";
import type { ChartController } from "../engine/controller";
import { useLiveCandles } from "../hooks/use-live-candles";
import { useChartStore } from "../store/chart-store";
import { useChartUiStore } from "../store/ui-store";
import { useDrawingStore } from "../store/drawing-store";
import { useIndicatorStore } from "../store/indicator-store";
import { useSessionStore } from "../store/session-store";
import { useViewportStore } from "../store/viewport-store";
import { useWatchlistStore } from "../store/watchlist-store";
import { workspaceService } from "../services/workspaceService";
import { AlertsStubDialog } from "./AlertsStubDialog";
import { BottomTimeline } from "./BottomTimeline";
import { ChartContainer } from "./ChartContainer";
import { DrawingContextMenu } from "./DrawingContextMenu";
import { IndicatorPanel } from "./IndicatorPanel";
import { LeftTools } from "./LeftTools";
import { SmartCursorHud } from "./SmartCursorHud";
import { StatusBar } from "./StatusBar";
import { TextEditOverlay } from "./TextEditOverlay";
import { TopToolbar } from "./TopToolbar";
import { WatchlistPanel } from "./WatchlistPanel";
import { IntelligenceSettingsPanel } from "./IntelligenceSettingsPanel";
import { DecisionSettingsPanel } from "./DecisionSettingsPanel";
import { CopilotPanel } from "../copilot/ui/CopilotPanel";
import { useLearningIntake } from "../../athena-learning/services/useLearningIntake";
import { preloadWatchlist } from "@/lib/candle-preload";
import { cn } from "@/lib/utils";

export function ChartTerminalLayout() {
  const rootRef = useRef<HTMLDivElement>(null);
  const engineRef = useRef<ChartController | null>(null);
  useLearningIntake();
  const symbol = useChartStore((s) => s.symbol);
  const timeframe = useChartStore((s) => s.timeframe);
  const setSymbol = useChartStore((s) => s.setSymbol);
  const setTimeframe = useChartStore((s) => s.setTimeframe);
  const {
    candles,
    liveCandle,
    loadOlder,
    hasMore,
    isLoadingMore,
    liveMode,
    setLiveMode,
  } = useLiveCandles(symbol, timeframe);
  const aiPanelOpen = useChartUiStore((s) => s.aiPanelOpen);
  const rightTab = useChartUiStore((s) => s.rightTab);
  const setRightTab = useChartUiStore((s) => s.setRightTab);
  const timelineVisible = useChartUiStore((s) => s.timelineVisible);
  const setFullscreen = useChartUiStore((s) => s.setFullscreen);
  const theme = useChartUiStore((s) => s.theme);
  const setTheme = useChartUiStore((s) => s.setTheme);
  const settingsOpen = useChartUiStore((s) => s.settingsOpen);
  const setSettingsOpen = useChartUiStore((s) => s.setSettingsOpen);
  const objects = useDrawingStore((s) => s.objects);
  const setObjects = useDrawingStore((s) => s.setObjects);
  const instances = useIndicatorStore((s) => s.instances);
  const setInstances = useIndicatorStore((s) => s.setInstances);
  const sessionsEnabled = useSessionStore((s) => s.enabled);
  const sessionFlags = useSessionStore((s) => s.flags);
  const setSessionsEnabled = useSessionStore((s) => s.setEnabled);
  const setSessionFlags = useSessionStore((s) => s.setFlags);
  const setViewport = useViewportStore((s) => s.setViewport);
  const viewportFrom = useViewportStore((s) => s.from);
  const viewportTo = useViewportStore((s) => s.to);
  const viewport = useMemo(
    () => ({ from: viewportFrom, to: viewportTo }),
    [viewportFrom, viewportTo],
  );
  const watchlist = useWatchlistStore((s) => s.items);
  const setWatchlist = useWatchlistStore((s) => s.setItems);
  const restoredViewportFor = useRef<string | null>(null);

  // Background-warm watchlist symbols for the active timeframe (non-blocking).
  useEffect(() => {
    if (!timeframe || watchlist.length === 0) return;
    const symbols = watchlist
      .map((item) => item.symbol)
      .filter((s) => s && s !== symbol);
    if (symbols.length === 0) return;
    const handle = window.setTimeout(() => {
      preloadWatchlist(symbols.slice(0, 12), timeframe);
    }, 750);
    return () => window.clearTimeout(handle);
  }, [symbol, timeframe, watchlist]);

  // Persist drawings per symbol (don't wipe on TF change)
  useEffect(() => {
    const key = `athena.chart.drawings.${symbol}`;
    try {
      const raw = localStorage.getItem(key);
      if (raw) setObjects(JSON.parse(raw));
      else setObjects([]);
    } catch {
      setObjects([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol]);

  useEffect(() => {
    try {
      localStorage.setItem(
        `athena.chart.drawings.${symbol}`,
        JSON.stringify(objects),
      );
    } catch {
      /* ignore */
    }
  }, [objects, symbol]);

  // Debounced workspace autosave (never persists candle arrays)
  useEffect(() => {
    const t = setTimeout(() => {
      workspaceService.save({
        version: 1,
        symbol,
        timeframe,
        theme,
        viewport,
        drawings: objects,
        indicators: instances,
        watchlist,
        sessionsEnabled,
        sessionFlags,
        liveMode,
        savedAt: Date.now(),
      });
    }, 800);
    return () => clearTimeout(t);
  }, [
    symbol,
    timeframe,
    theme,
    viewport,
    objects,
    instances,
    watchlist,
    sessionsEnabled,
    sessionFlags,
    liveMode,
  ]);

  // Restore viewport from workspace once per symbol (not candle cache)
  useEffect(() => {
    if (candles.length === 0) return;
    if (restoredViewportFor.current === symbol) return;
    const ws = workspaceService.load();
    if (!ws?.viewport || ws.symbol !== symbol) {
      restoredViewportFor.current = symbol;
      return;
    }
    const eng = engineRef.current;
    if (!eng) return;
    restoredViewportFor.current = symbol;
    setViewport(ws.viewport);
    eng.restoreViewport(ws.viewport.from, ws.viewport.to, candles.length);
    if (ws.liveMode === false) {
      setLiveMode(false);
      eng.setLiveMode(false);
    } else {
      setLiveMode(true);
      eng.goLive();
    }
  }, [candles.length, symbol, setViewport, setLiveMode]);

  const onGoLive = useCallback(() => {
    setLiveMode(true);
    engineRef.current?.goLive();
  }, [setLiveMode]);

  const onFullscreen = useCallback(() => {
    const el = rootRef.current;
    if (!el) return;
    if (document.fullscreenElement) {
      void document.exitFullscreen();
      setFullscreen(false);
    } else {
      void el.requestFullscreen();
      setFullscreen(true);
    }
  }, [setFullscreen]);

  const onScreenshot = useCallback(() => {
    const url = engineRef.current?.exportPng({ hideChrome: true });
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = `athena-chart-${symbol}-${timeframe}.png`;
    a.click();
  }, [symbol, timeframe]);

  const onSaveWorkspace = useCallback(() => {
    workspaceService.save({
      version: 1,
      symbol,
      timeframe,
      theme,
      viewport,
      drawings: objects,
      indicators: instances,
      watchlist,
      sessionsEnabled,
      sessionFlags,
      liveMode,
      savedAt: Date.now(),
    });
  }, [
    symbol,
    timeframe,
    theme,
    viewport,
    objects,
    instances,
    watchlist,
    sessionsEnabled,
    sessionFlags,
    liveMode,
  ]);

  const onLoadWorkspace = useCallback(() => {
    const ws = workspaceService.load();
    if (!ws) return;
    setSymbol(ws.symbol);
    setTimeframe(ws.timeframe);
    setTheme(ws.theme);
    setObjects(ws.drawings);
    setInstances(ws.indicators);
    setWatchlist(ws.watchlist);
    setSessionsEnabled(ws.sessionsEnabled);
    setSessionFlags(ws.sessionFlags);
    setViewport(ws.viewport);
    restoredViewportFor.current = null;
    if (ws.liveMode != null) setLiveMode(ws.liveMode);
  }, [
    setSymbol,
    setTimeframe,
    setTheme,
    setObjects,
    setInstances,
    setWatchlist,
    setSessionsEnabled,
    setSessionFlags,
    setViewport,
    setLiveMode,
  ]);

  return (
    <TooltipProvider delayDuration={200}>
      <div
        ref={rootRef}
        className="relative flex h-screen w-screen flex-col overflow-hidden bg-background text-foreground"
      >
        <TopToolbar
          onFullscreen={onFullscreen}
          onScreenshot={onScreenshot}
          onSaveWorkspace={onSaveWorkspace}
          onLoadWorkspace={onLoadWorkspace}
          onGoLive={onGoLive}
          liveMode={liveMode}
        />
        <div className="flex min-h-0 flex-1">
          <LeftTools />
          <div className="relative flex min-w-0 flex-1 flex-col">
            <ChartContainer
              candles={candles}
              liveCandle={liveCandle}
              engineRef={engineRef}
              onNeedMoreHistory={hasMore ? loadOlder : undefined}
              isLoadingHistory={isLoadingMore}
              hasMoreHistory={hasMore}
              liveMode={liveMode}
            />
            <SmartCursorHud />
            <IndicatorPanel />
            <TextEditOverlay engineRef={engineRef} />
            <AlertsStubDialog />
            <IntelligenceSettingsPanel
              open={settingsOpen}
              onClose={() => setSettingsOpen(false)}
            />
            <DecisionSettingsPanel
              open={settingsOpen}
              onClose={() => setSettingsOpen(false)}
            />
            {timelineVisible ? <BottomTimeline /> : null}
            <StatusBar />
          </div>
          {aiPanelOpen ? (
            <aside className="flex w-96 shrink-0 flex-col border-l border-border bg-[#0a0a0a]">
              <div className="flex h-9 items-center gap-1 border-b border-border px-2">
                <button
                  type="button"
                  onClick={() => setRightTab("watchlist")}
                  className={cn(
                    "rounded-sm px-2 py-1 text-[10px] uppercase tracking-wide",
                    rightTab === "watchlist"
                      ? "bg-primary/15 text-primary"
                      : "text-muted hover:text-foreground",
                  )}
                >
                  Watchlist
                </button>
                <button
                  type="button"
                  onClick={() => setRightTab("ai")}
                  className={cn(
                    "rounded-sm px-2 py-1 text-[10px] uppercase tracking-wide",
                    rightTab === "ai"
                      ? "bg-primary/15 text-primary"
                      : "text-muted hover:text-foreground",
                  )}
                >
                  Copilot
                </button>
              </div>
              <div className="min-h-0 flex-1 overflow-hidden">
                {rightTab === "watchlist" ? (
                  <WatchlistPanel />
                ) : (
                  <CopilotPanel candles={candles} />
                )}
              </div>
            </aside>
          ) : null}
        </div>
        <DrawingContextMenu engineRef={engineRef} />
      </div>
    </TooltipProvider>
  );
}
