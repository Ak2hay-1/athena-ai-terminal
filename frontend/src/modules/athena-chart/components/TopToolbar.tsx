"use client";

import {
  Bell,
  Brain,
  Camera,
  Globe2,
  LayoutGrid,
  List,
  Maximize2,
  Moon,
  Play,
  Save,
  Search,
  Settings,
  Sun,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useChartUiStore } from "../store/ui-store";
import { useReplayStore } from "../store/replay-store";
import { useSessionStore } from "../store/session-store";
import { useAlertStore } from "../store/alert-store";
import { IndicatorMenu } from "./IndicatorMenu";
import { PairSelector, TimeframeSelector } from "./PairSelector";

function IconBtn({
  label,
  active,
  onClick,
  children,
}: {
  label: string;
  active?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          aria-label={label}
          onClick={onClick}
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-sm border text-muted",
            active
              ? "border-primary/40 bg-primary/10 text-primary"
              : "border-border hover:text-foreground",
          )}
        >
          {children}
        </button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}

interface TopToolbarProps {
  onScreenshot?: () => void;
  onFullscreen?: () => void;
  onSaveWorkspace?: () => void;
  onLoadWorkspace?: () => void;
  onGoLive?: () => void;
  liveMode?: boolean;
}

export function TopToolbar({
  onScreenshot,
  onFullscreen,
  onSaveWorkspace,
  onLoadWorkspace,
  onGoLive,
  liveMode = true,
}: TopToolbarProps) {
  const aiPanelOpen = useChartUiStore((s) => s.aiPanelOpen);
  const toggleAiPanel = useChartUiStore((s) => s.toggleAiPanel);
  const setRightTab = useChartUiStore((s) => s.setRightTab);
  const rightTab = useChartUiStore((s) => s.rightTab);
  const theme = useChartUiStore((s) => s.theme);
  const toggleTheme = useChartUiStore((s) => s.toggleTheme);
  const setSearchOpen = useChartUiStore((s) => s.setSearchOpen);
  const setSettingsOpen = useChartUiStore((s) => s.setSettingsOpen);
  const layoutMode = useChartUiStore((s) => s.layoutMode);
  const setLayoutMode = useChartUiStore((s) => s.setLayoutMode);
  const replayEnabled = useReplayStore((s) => s.enabled);
  const setReplayEnabled = useReplayStore((s) => s.setEnabled);
  const sessionsEnabled = useSessionStore((s) => s.enabled);
  const setSessionsEnabled = useSessionStore((s) => s.setEnabled);
  const setDraftOpen = useAlertStore((s) => s.setDraftOpen);

  return (
    <header className="flex h-10 shrink-0 items-center gap-3 border-b border-border bg-[#080808] px-2">
      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-primary">
          Athena Chart
        </span>
        <PairSelector />
        <TimeframeSelector />
      </div>

      <div className="ml-auto flex items-center gap-1">
        <button
          type="button"
          onClick={onGoLive}
          className={cn(
            "h-7 rounded-sm border px-2 font-mono text-[10px] uppercase tracking-wide",
            liveMode
              ? "border-primary/40 bg-primary/10 text-primary"
              : "border-border text-muted hover:text-foreground",
          )}
        >
          Live
        </button>
        <IndicatorMenu />
        <IconBtn
          label="Sessions"
          active={sessionsEnabled}
          onClick={() => setSessionsEnabled(!sessionsEnabled)}
        >
          <Globe2 className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn
          label="Alerts"
          onClick={() => setDraftOpen(true)}
        >
          <Bell className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn
          label="Replay"
          active={replayEnabled}
          onClick={() => setReplayEnabled(!replayEnabled)}
        >
          <Play className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn
          label="Layout"
          active={layoutMode === "split"}
          onClick={() =>
            setLayoutMode(layoutMode === "single" ? "split" : "single")
          }
        >
          <LayoutGrid className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn
          label="Watchlist"
          active={aiPanelOpen && rightTab === "watchlist"}
          onClick={() => setRightTab("watchlist")}
        >
          <List className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn
          label="AI Panel"
          active={aiPanelOpen && rightTab === "ai"}
          onClick={() => {
            setRightTab("ai");
            if (!aiPanelOpen) toggleAiPanel();
          }}
        >
          <Brain className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn label="Save workspace" onClick={onSaveWorkspace}>
          <Save className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn label="Theme" onClick={toggleTheme}>
          {theme === "dark" ? (
            <Moon className="h-3.5 w-3.5" />
          ) : (
            <Sun className="h-3.5 w-3.5" />
          )}
        </IconBtn>
        <IconBtn label="Fullscreen" onClick={onFullscreen}>
          <Maximize2 className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn label="Screenshot" onClick={onScreenshot}>
          <Camera className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn label="Settings" onClick={() => setSettingsOpen(true)}>
          <Settings className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn label="Search" onClick={() => setSearchOpen(true)}>
          <Search className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn label="Load workspace" onClick={onLoadWorkspace}>
          <Save className="h-3.5 w-3.5 opacity-50" />
        </IconBtn>
      </div>
    </header>
  );
}
