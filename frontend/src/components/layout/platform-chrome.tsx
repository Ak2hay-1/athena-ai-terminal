"use client";

import { usePathname } from "next/navigation";
import { AppShell } from "./app-shell";

/**
 * Renders AppShell for normal platform pages.
 * /chart launches the chrome-free Athena Chart terminal.
 */
export function PlatformChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isChartTerminal =
    pathname === "/chart" || pathname.startsWith("/chart/");

  if (isChartTerminal) {
    return <div className="h-screen w-screen overflow-hidden bg-background">{children}</div>;
  }

  return <AppShell>{children}</AppShell>;
}
