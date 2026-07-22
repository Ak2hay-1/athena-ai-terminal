import { apiFetch } from "@/services/api-client";
import { relativeTime } from "@/lib/mappers";

export type NotificationDelivery = {
  id: number;
  channel: string;
  messageType: string;
  priority: string;
  status: string;
  payload: Record<string, unknown>;
  latencyMs: number | null;
  createdAt: string | null;
  openedAt: string | null;
  clickedAt: string | null;
  dismissedAt: string | null;
};

type NotificationRaw = {
  id: number;
  channel: string;
  message_type: string;
  priority: string;
  status: string;
  payload: Record<string, unknown>;
  latency_ms: number | null;
  created_at: string | null;
  opened_at: string | null;
  clicked_at: string | null;
  dismissed_at: string | null;
};

function mapNotification(raw: NotificationRaw): NotificationDelivery {
  return {
    id: raw.id,
    channel: raw.channel,
    messageType: raw.message_type,
    priority: raw.priority,
    status: raw.status,
    payload: raw.payload ?? {},
    latencyMs: raw.latency_ms,
    createdAt: raw.created_at,
    openedAt: raw.opened_at,
    clickedAt: raw.clicked_at,
    dismissedAt: raw.dismissed_at,
  };
}

export function notificationTitle(item: NotificationDelivery): string {
  const payload = item.payload;
  const title =
    (typeof payload.title === "string" && payload.title) ||
    (typeof payload.subject === "string" && payload.subject) ||
    (typeof payload.message === "string" && payload.message) ||
    item.messageType;
  return title;
}

export function notificationDetail(item: NotificationDelivery): string {
  const payload = item.payload;
  if (typeof payload.body === "string") return payload.body;
  if (typeof payload.detail === "string") return payload.detail;
  if (typeof payload.message === "string" && payload.message !== notificationTitle(item)) {
    return payload.message;
  }
  return `${item.channel} · ${item.priority}`;
}

export function notificationTime(item: NotificationDelivery): string {
  return item.createdAt ? relativeTime(item.createdAt) : "—";
}

export function isUnreadNotification(item: NotificationDelivery): boolean {
  return !item.openedAt && !item.dismissedAt;
}

export async function getRecentNotifications(
  limit = 50,
): Promise<NotificationDelivery[]> {
  const raw = await apiFetch<NotificationRaw[]>(
    `/notifications/recent?limit=${Math.max(1, Math.min(limit, 200))}`,
  );
  return raw.map(mapNotification);
}

export async function interactNotification(
  id: number,
  action: "opened" | "clicked" | "dismissed",
): Promise<NotificationDelivery> {
  const raw = await apiFetch<NotificationRaw>(`/notifications/${id}/interact`, {
    method: "POST",
    body: JSON.stringify({ action }),
  });
  return mapNotification(raw);
}
