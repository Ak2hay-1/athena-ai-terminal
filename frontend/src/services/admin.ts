import { apiFetch } from "@/services/api-client";
import type {
  AdminOverview,
  AdminSchedulers,
  LearningRetrainResult,
  SchedulerTriggerResult,
  User,
  UserRole,
} from "@/types";

export type AdminUserUpdate = {
  email?: string;
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
  is_verified?: boolean;
};

export async function getAdminOverview(): Promise<AdminOverview> {
  return apiFetch<AdminOverview>("/admin/overview");
}

export async function getAdminSchedulers(): Promise<AdminSchedulers> {
  return apiFetch<AdminSchedulers>("/admin/schedulers");
}

export async function triggerMarketCollection(
  timeframe: string,
): Promise<SchedulerTriggerResult> {
  const search = new URLSearchParams({ timeframe });
  return apiFetch<SchedulerTriggerResult>(
    `/admin/schedulers/market/run?${search}`,
    { method: "POST" },
  );
}

export async function triggerSchedulerJob(
  jobId: string,
): Promise<SchedulerTriggerResult> {
  return apiFetch<SchedulerTriggerResult>(
    `/admin/schedulers/jobs/${encodeURIComponent(jobId)}/run`,
    { method: "POST" },
  );
}

export async function syncNewsFeeds(): Promise<{ inserted: number }> {
  return apiFetch<{ inserted: number }>("/admin/news/sync", {
    method: "POST",
  });
}

export async function cleanupMarketCandles(
  before: string,
): Promise<{ deleted: number; before: string }> {
  const search = new URLSearchParams({ before });
  return apiFetch<{ deleted: number; before: string }>(
    `/admin/market/cleanup?${search}`,
    { method: "DELETE" },
  );
}

export async function listUsers(params?: {
  skip?: number;
  limit?: number;
}): Promise<User[]> {
  const search = new URLSearchParams();
  if (params?.skip != null) search.set("skip", String(params.skip));
  if (params?.limit != null) search.set("limit", String(params.limit));
  const query = search.toString();
  return apiFetch<User[]>(`/auth/users${query ? `?${query}` : ""}`);
}

export async function getUser(userId: number): Promise<User> {
  return apiFetch<User>(`/auth/users/${userId}`);
}

export async function updateUser(
  userId: number,
  payload: AdminUserUpdate,
): Promise<User> {
  return apiFetch<User>(`/auth/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function updateUserRole(
  userId: number,
  role: UserRole,
): Promise<User> {
  return apiFetch<User>(`/auth/users/${userId}/role`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export async function activateUser(userId: number): Promise<User> {
  return apiFetch<User>(`/auth/users/${userId}/activate`, {
    method: "PATCH",
  });
}

export async function deactivateUser(userId: number): Promise<User> {
  return apiFetch<User>(`/auth/users/${userId}/deactivate`, {
    method: "PATCH",
  });
}

export async function getLearningStats(
  symbol = "XAUUSD",
  timeframe = "M1",
): Promise<Record<string, unknown>> {
  const search = new URLSearchParams({ symbol, timeframe });
  return apiFetch<Record<string, unknown>>(`/learning/stats?${search}`);
}

export async function retrainLearning(): Promise<LearningRetrainResult[]> {
  return apiFetch<LearningRetrainResult[]>("/learning/retrain", {
    method: "POST",
  });
}

export async function labelLearningOutcomes(): Promise<{ labeled: number }> {
  return apiFetch<{ labeled: number }>("/learning/label", {
    method: "POST",
  });
}

export async function getMt5Status(): Promise<AdminOverview["mt5"]> {
  return apiFetch<AdminOverview["mt5"]>("/mt5/status");
}

export async function initializeMt5(): Promise<boolean> {
  return apiFetch<boolean>("/mt5/initialize", { method: "POST" });
}

export async function shutdownMt5(): Promise<{ success: boolean; message: string }> {
  return apiFetch<{ success: boolean; message: string }>("/mt5/shutdown", {
    method: "POST",
  });
}
