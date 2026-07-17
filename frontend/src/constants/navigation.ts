export const APP_NAME = "Athena";
export const APP_TAGLINE = "AI Trading Intelligence";

export const colors = {
  background: "#09090b",
  sidebar: "#111114",
  panel: "#141418",
  border: "#27272a",
  primary: "#3b82f6",
  bullish: "#22c55e",
  bearish: "#ef4444",
  warning: "#f59e0b",
  ai: "#a855f7",
  muted: "#a1a1aa",
} as const;

export type NavItem = {
  label: string;
  href: string;
  icon:
    | "layout-dashboard"
    | "line-chart"
    | "sparkles"
    | "scan"
    | "history"
    | "book-open"
    | "bar-chart-3"
    | "bell"
    | "target"
    | "flask-conical"
    | "settings"
    | "message-square"
    | "shield"
    | "users"
    | "activity";
};

export const primaryNav: NavItem[] = [
  { label: "Dashboard", href: "/", icon: "layout-dashboard" },
  { label: "Markets", href: "/markets", icon: "line-chart" },
  { label: "Athena AI", href: "/ai", icon: "sparkles" },
  { label: "Scanner", href: "/scanner", icon: "scan" },
  { label: "History", href: "/history", icon: "history" },
  { label: "Journal", href: "/journal", icon: "book-open" },
  { label: "Analytics", href: "/analytics", icon: "bar-chart-3" },
  { label: "Strategies", href: "/strategies", icon: "target" },
  { label: "Alerts", href: "/alerts", icon: "bell" },
  { label: "Settings", href: "/settings", icon: "settings" },
];

export const adminNav: NavItem[] = [
  { label: "Admin", href: "/admin", icon: "shield" },
  { label: "Users", href: "/admin/users", icon: "users" },
  { label: "Ops", href: "/admin/ops", icon: "activity" },
];
