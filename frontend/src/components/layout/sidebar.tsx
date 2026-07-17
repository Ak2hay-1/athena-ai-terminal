"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Bell,
  BookOpen,
  FlaskConical,
  History,
  LayoutDashboard,
  LineChart,
  MessageSquare,
  Scan,
  Settings,
  Shield,
  Sparkles,
  Target,
  Users,
  type LucideIcon,
} from "lucide-react";
import { APP_NAME, adminNav, primaryNav, type NavItem } from "@/constants/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";
import { useUiStore } from "@/store/ui-store";

const iconMap: Record<NavItem["icon"], LucideIcon> = {
  "layout-dashboard": LayoutDashboard,
  "line-chart": LineChart,
  sparkles: Sparkles,
  scan: Scan,
  history: History,
  "book-open": BookOpen,
  "bar-chart-3": BarChart3,
  bell: Bell,
  target: Target,
  "flask-conical": FlaskConical,
  settings: Settings,
  "message-square": MessageSquare,
  shield: Shield,
  users: Users,
  activity: Activity,
};

function NavLinkItem({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const pathname = usePathname();
  const active =
    item.href === "/"
      ? pathname === "/"
      : item.href === "/admin"
        ? pathname === "/admin"
        : pathname === item.href || pathname.startsWith(`${item.href}/`);
  const Icon = iconMap[item.icon];

  return (
    <Link
      href={item.href}
      className={cn(
        "group flex items-center gap-3 rounded-sm px-3 py-2 text-sm transition-colors",
        active
          ? "border-l-2 border-primary bg-primary/10 text-primary"
          : "border-l-2 border-transparent text-muted hover:bg-panel-elevated hover:text-foreground",
        collapsed && "justify-center px-2",
      )}
      title={collapsed ? item.label : undefined}
    >
      <Icon
        className={cn(
          "h-4 w-4 shrink-0",
          active ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
        )}
      />
      {!collapsed ? <span className="truncate">{item.label}</span> : null}
    </Link>
  );
}

export function Sidebar() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const mobileNavOpen = useUiStore((s) => s.mobileNavOpen);
  const setMobileNavOpen = useUiStore((s) => s.setMobileNavOpen);
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "ADMIN";

  return (
    <>
      {mobileNavOpen ? (
        <button
          type="button"
          aria-label="Close navigation"
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={() => setMobileNavOpen(false)}
        />
      ) : null}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col border-r border-border bg-sidebar transition-all duration-200",
          collapsed ? "w-[68px]" : "w-60",
          mobileNavOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        )}
      >
        <div
          className={cn(
            "flex h-14 items-center border-b border-border px-4",
            collapsed && "justify-center px-2",
          )}
        >
          <Link href="/" className="flex items-center gap-2.5" onClick={() => setMobileNavOpen(false)}>
            <span className="flex h-8 w-8 items-center justify-center rounded-sm bg-primary text-sm font-bold text-primary-foreground">
              A
            </span>
            {!collapsed ? (
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold tracking-tight">{APP_NAME}</p>
                <p className="truncate text-[10px] uppercase tracking-[0.16em] text-primary">
                  Terminal
                </p>
              </div>
            ) : null}
          </Link>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
          {primaryNav.map((item) => (
            <div key={item.href} onClick={() => setMobileNavOpen(false)}>
              <NavLinkItem item={item} collapsed={collapsed} />
            </div>
          ))}

          {isAdmin ? (
            <div className="pt-3">
              {!collapsed ? (
                <p className="mb-1 px-3 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
                  Administration
                </p>
              ) : (
                <div className="mx-auto mb-1 h-px w-6 bg-border" />
              )}
              {adminNav.map((item) => (
                <div key={item.href} onClick={() => setMobileNavOpen(false)}>
                  <NavLinkItem item={item} collapsed={collapsed} />
                </div>
              ))}
            </div>
          ) : null}
        </nav>

        <div className={cn("border-t border-border p-3", collapsed && "px-2")}>
          <div
            className={cn(
              "rounded-sm border border-primary/25 bg-primary/5 px-3 py-2.5",
              collapsed && "flex justify-center px-2 py-2",
            )}
          >
            {collapsed ? (
              <Sparkles className="h-4 w-4 text-primary" />
            ) : (
              <>
                <p className="text-xs font-medium text-primary">Athena AI online</p>
                <p className="mt-0.5 text-[11px] text-muted">Market intelligence desk</p>
              </>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
