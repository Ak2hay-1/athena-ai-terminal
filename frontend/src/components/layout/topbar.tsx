"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Bell,
  LogOut,
  Menu,
  PanelRightClose,
  PanelRightOpen,
  Search,
  Sparkles,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { adminNav, primaryNav } from "@/constants/navigation";
import { useDerivedAlerts } from "@/features/alerts/hooks/use-derived-alerts";
import {
  getRecentNotifications,
  isUnreadNotification,
} from "@/services/notifications";
import { useAuthStore } from "@/store/auth-store";
import { useUiStore } from "@/store/ui-store";
import { AutoTradeControl } from "@/features/trading/components/auto-trade-control";

interface TopbarProps {
  title?: string;
  subtitle?: string;
}

function titleFromPath(pathname: string) {
  if (pathname === "/") return "Dashboard";
  const adminMatch = adminNav.find(
    (item) =>
      item.href === pathname ||
      (item.href !== "/admin" && pathname.startsWith(`${item.href}/`)) ||
      (item.href === "/admin" && pathname === "/admin"),
  );
  if (adminMatch) return adminMatch.label;
  if (pathname.startsWith("/admin")) return "Admin";
  const match = primaryNav.find(
    (item) =>
      item.href !== "/" &&
      (pathname === item.href || pathname.startsWith(`${item.href}/`)),
  );
  if (match) return match.label;
  if (pathname.startsWith("/recommendations")) return "Recommendation";
  return "Athena";
}

export function Topbar({ title, subtitle }: TopbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const resolvedTitle = title ?? titleFromPath(pathname);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);
  const setMobileNavOpen = useUiStore((s) => s.setMobileNavOpen);
  const rightPanel = useUiStore((s) => s.rightPanel);
  const toggleRightPanel = useUiStore((s) => s.toggleRightPanel);
  const setNotificationsOpen = useUiStore((s) => s.setNotificationsOpen);
  const setSearchOpen = useUiStore((s) => s.setSearchOpen);

  const { highCount } = useDerivedAlerts({ enabled: Boolean(user) });
  const inboxQuery = useQuery({
    queryKey: ["notifications", "recent"],
    queryFn: () => getRecentNotifications(40),
    enabled: Boolean(user),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
  const unreadInbox = (inboxQuery.data ?? []).filter(isUnreadNotification).length;
  const badgeCount = highCount + unreadInbox;

  const initials = (user?.full_name || user?.username || "AT")
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="sticky top-0 z-30 flex h-12 items-center justify-between gap-4 border-b border-border bg-background/95 px-4 lg:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={() => setMobileNavOpen(true)}
          aria-label="Open menu"
        >
          <Menu className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="hidden lg:inline-flex"
          onClick={toggleSidebar}
          aria-label="Toggle sidebar"
        >
          <Menu className="h-4 w-4" />
        </Button>
        <div className="min-w-0">
          <h1 className="truncate text-sm font-semibold tracking-tight">
            {resolvedTitle}
          </h1>
          {subtitle ? (
            <p className="truncate text-xs text-muted">{subtitle}</p>
          ) : null}
        </div>
      </div>

      <div className="hidden max-w-md flex-1 md:block">
        <button
          type="button"
          onClick={() => setSearchOpen(true)}
          className="relative flex h-8 w-full items-center rounded-sm border border-border bg-panel pr-3 pl-9 text-left text-sm text-muted-foreground outline-none transition-colors hover:border-primary/50"
        >
          <Search className="pointer-events-none absolute top-1/2 left-3 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <span className="truncate">Search markets, recommendations, journals…</span>
          <kbd className="ml-auto hidden rounded-sm border border-border px-1.5 py-0.5 text-[10px] lg:inline">
            Ctrl K
          </kbd>
        </button>
      </div>

      <div className="flex items-center gap-1.5">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => setSearchOpen(true)}
          aria-label="Search"
        >
          <Search className="h-4 w-4" />
        </Button>
        <AutoTradeControl />
        <Button variant="ai" size="sm" className="hidden sm:inline-flex" asChild>
          <Link href="/ai">
            <Sparkles className="h-3.5 w-3.5" />
            Ask Athena
          </Link>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setNotificationsOpen(true)}
          aria-label="Notifications"
          className="relative"
        >
          <Bell className="h-4 w-4" />
          {badgeCount > 0 ? (
            <span className="absolute top-1 right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-warning px-1 text-[9px] font-semibold text-black">
              {badgeCount > 9 ? "9+" : badgeCount}
            </span>
          ) : null}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleRightPanel}
          aria-label="Toggle AI panel"
          className="hidden xl:inline-flex"
        >
          {rightPanel === "assistant" ? (
            <PanelRightClose className="h-4 w-4" />
          ) : (
            <PanelRightOpen className="h-4 w-4" />
          )}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Log out"
          onClick={() => {
            logout();
            router.replace("/login");
          }}
        >
          <LogOut className="h-4 w-4" />
        </Button>
        <div className="ml-1 flex h-8 w-8 items-center justify-center rounded-sm border border-border bg-panel-elevated text-xs font-medium">
          {initials}
        </div>
      </div>
    </header>
  );
}
