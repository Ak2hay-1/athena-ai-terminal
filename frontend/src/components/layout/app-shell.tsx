"use client";

import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui-store";
import { AiAssistantPanel } from "./ai-assistant-panel";
import { GlobalSearch } from "./global-search";
import { NotificationsDrawer } from "./notifications-drawer";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

interface AppShellProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
}

export function AppShell({ children, title, subtitle }: AppShellProps) {
  const sidebarCollapsed = useUiStore((s) => s.sidebarCollapsed);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div
        className={cn(
          "flex min-h-screen flex-col transition-[padding] duration-200",
          sidebarCollapsed ? "lg:pl-[68px]" : "lg:pl-60",
        )}
      >
        <Topbar title={title} subtitle={subtitle} />
        <div className="flex flex-1">
          <main className="min-w-0 flex-1 overflow-x-hidden px-4 py-6 lg:px-6">
            {children}
          </main>
          <AiAssistantPanel />
        </div>
        <footer className="border-t border-border px-4 py-2 text-[11px] text-muted-foreground lg:px-6">
          Athena · Professional market intelligence · Not a broker
        </footer>
      </div>
      <NotificationsDrawer />
      <GlobalSearch />
    </div>
  );
}
