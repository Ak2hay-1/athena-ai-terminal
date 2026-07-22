"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Newspaper, ShieldAlert, TrendingUp, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  useDerivedAlerts,
  type AlertItem,
} from "@/features/alerts/hooks/use-derived-alerts";
import { cn } from "@/lib/utils";
import {
  getRecentNotifications,
  interactNotification,
  isUnreadNotification,
  notificationDetail,
  notificationTime,
  notificationTitle,
} from "@/services/notifications";
import { useAuthStore } from "@/store/auth-store";
import { useUiStore } from "@/store/ui-store";

type DrawerTab = "alerts" | "inbox";

function iconFor(kind: AlertItem["kind"]) {
  if (kind === "news") return Newspaper;
  if (kind === "signal") return TrendingUp;
  if (kind === "structure") return ShieldAlert;
  return Bell;
}

export function NotificationsDrawer() {
  const open = useUiStore((s) => s.notificationsOpen);
  const setOpen = useUiStore((s) => s.setNotificationsOpen);
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<DrawerTab>("alerts");

  const { alerts, highCount } = useDerivedAlerts({
    enabled: open && Boolean(user),
  });

  const inboxQuery = useQuery({
    queryKey: ["notifications", "recent"],
    queryFn: () => getRecentNotifications(40),
    enabled: open && Boolean(user),
    refetchInterval: open ? 30_000 : false,
  });

  const interactMutation = useMutation({
    mutationFn: ({
      id,
      action,
    }: {
      id: number;
      action: "opened" | "clicked" | "dismissed";
    }) => interactNotification(id, action),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  useEffect(() => {
    if (!open) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, setOpen]);

  if (!open) return null;

  const inbox = inboxQuery.data ?? [];
  const unreadCount = inbox.filter(isUnreadNotification).length;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        className="absolute inset-0 bg-black/50"
        aria-label="Close notifications"
        onClick={() => setOpen(false)}
      />
      <aside className="relative flex h-full w-full max-w-md flex-col border-l border-border bg-sidebar shadow-xl">
        <div className="flex h-12 shrink-0 items-center justify-between border-b border-border px-4">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-primary" />
            <p className="text-sm font-semibold">Notifications</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Close"
            onClick={() => setOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex border-b border-border">
          <button
            type="button"
            className={cn(
              "flex-1 px-3 py-2.5 text-sm font-medium",
              tab === "alerts"
                ? "border-b-2 border-primary text-foreground"
                : "text-muted hover:text-foreground",
            )}
            onClick={() => setTab("alerts")}
          >
            Alerts
            {highCount > 0 ? (
              <span className="ml-2 text-[11px] text-warning">{highCount}</span>
            ) : null}
          </button>
          <button
            type="button"
            className={cn(
              "flex-1 px-3 py-2.5 text-sm font-medium",
              tab === "inbox"
                ? "border-b-2 border-primary text-foreground"
                : "text-muted hover:text-foreground",
            )}
            onClick={() => setTab("inbox")}
          >
            Inbox
            {unreadCount > 0 ? (
              <span className="ml-2 text-[11px] text-primary">{unreadCount}</span>
            ) : null}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3">
          {tab === "alerts" ? (
            <div className="space-y-2">
              {alerts.length === 0 ? (
                <p className="py-10 text-center text-sm text-muted">
                  No derived alerts right now.
                </p>
              ) : (
                alerts.map((alert) => {
                  const Icon = iconFor(alert.kind);
                  return (
                    <div
                      key={alert.id}
                      className="rounded-sm border border-border/70 bg-background/30 px-3 py-3"
                    >
                      <div className="flex gap-2">
                        <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-sm font-medium">{alert.title}</p>
                            <Badge
                              tone={
                                alert.severity === "high"
                                  ? "warning"
                                  : alert.severity === "medium"
                                    ? "primary"
                                    : "neutral"
                              }
                            >
                              {alert.severity}
                            </Badge>
                          </div>
                          <p className="mt-1 text-xs text-muted">{alert.detail}</p>
                          <p className="mt-1 text-[11px] text-muted">{alert.time}</p>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {inboxQuery.isLoading ? (
                <p className="py-10 text-center text-sm text-muted">Loading inbox…</p>
              ) : inbox.length === 0 ? (
                <p className="py-10 text-center text-sm text-muted">
                  No delivered notifications yet.
                </p>
              ) : (
                inbox.map((item) => {
                  const unread = isUnreadNotification(item);
                  return (
                    <div
                      key={item.id}
                      className={cn(
                        "rounded-sm border px-3 py-3",
                        unread
                          ? "border-primary/40 bg-primary/5"
                          : "border-border/70 bg-background/30",
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium">
                          {notificationTitle(item)}
                        </p>
                        <Badge tone={unread ? "primary" : "neutral"}>
                          {item.priority}
                        </Badge>
                      </div>
                      <p className="mt-1 text-xs text-muted">
                        {notificationDetail(item)}
                      </p>
                      <p className="mt-1 text-[11px] text-muted">
                        {notificationTime(item)} · {item.channel}
                      </p>
                      <div className="mt-2 flex gap-2">
                        {unread ? (
                          <Button
                            size="sm"
                            variant="secondary"
                            disabled={interactMutation.isPending}
                            onClick={() =>
                              interactMutation.mutate({
                                id: item.id,
                                action: "opened",
                              })
                            }
                          >
                            Mark read
                          </Button>
                        ) : null}
                        {!item.dismissedAt ? (
                          <Button
                            size="sm"
                            variant="ghost"
                            disabled={interactMutation.isPending}
                            onClick={() =>
                              interactMutation.mutate({
                                id: item.id,
                                action: "dismissed",
                              })
                            }
                          >
                            Dismiss
                          </Button>
                        ) : null}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>

        <div className="border-t border-border p-3">
          <Button asChild variant="secondary" className="w-full">
            <Link href="/alerts" onClick={() => setOpen(false)}>
              View all alerts
            </Link>
          </Button>
        </div>
      </aside>
    </div>
  );
}
