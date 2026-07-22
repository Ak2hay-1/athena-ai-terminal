import { apiFetch } from "@/services/api-client";

export interface DisclaimerStatus {
  accepted: boolean;
  accepted_at: string | null;
  disclaimer_version: string | null;
  app_version: string | null;
  required_version: string;
}

export async function getDisclaimerStatus(): Promise<DisclaimerStatus> {
  return apiFetch<DisclaimerStatus>("/disclaimer");
}

export async function acceptDisclaimer(payload: {
  app_version: string;
  disclaimer_version: string;
}): Promise<DisclaimerStatus> {
  return apiFetch<DisclaimerStatus>("/disclaimer/accept", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
