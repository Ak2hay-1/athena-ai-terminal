import { apiFetch } from "@/services/api-client";
import type { HealthStatus } from "@/types";

export async function getHealth(): Promise<HealthStatus> {
  return apiFetch<HealthStatus>("/health");
}
