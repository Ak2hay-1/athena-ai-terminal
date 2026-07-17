import { apiFetch, clearTokens, setTokens } from "@/services/api-client";
import type { TokenResponse, User } from "@/types";
import { config } from "@/lib/config";

export async function login(
  username: string,
  password: string,
): Promise<TokenResponse> {
  const url = `${config.apiUrl}/auth/login`;
  // #region agent log
  fetch("http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Debug-Session-Id": "9c9447",
    },
    body: JSON.stringify({
      sessionId: "9c9447",
      runId: "pre-fix",
      hypothesisId: "B",
      location: "auth.ts:login:before",
      message: "login fetch starting",
      data: { url, apiUrl: config.apiUrl },
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
  } catch (err) {
    // #region agent log
    fetch("http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "9c9447",
      },
      body: JSON.stringify({
        sessionId: "9c9447",
        runId: "pre-fix",
        hypothesisId: "B",
        location: "auth.ts:login:network_error",
        message: "login fetch threw",
        data: {
          url,
          error: err instanceof Error ? err.message : String(err),
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    throw err;
  }

  // #region agent log
  fetch("http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Debug-Session-Id": "9c9447",
    },
    body: JSON.stringify({
      sessionId: "9c9447",
      runId: "pre-fix",
      hypothesisId: "B",
      location: "auth.ts:login:after",
      message: "login fetch completed",
      data: { url, status: response.status, ok: response.ok },
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion

  if (!response.ok) {
    throw new Error("Invalid credentials");
  }

  const tokens = (await response.json()) as TokenResponse;
  setTokens(tokens);
  return tokens;
}

export async function register(payload: {
  username: string;
  email: string;
  full_name: string;
  password: string;
}): Promise<User> {
  return apiFetch<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getMe(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export async function updateMe(payload: {
  email?: string;
  full_name?: string;
}): Promise<User> {
  return apiFetch<User>("/auth/me", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function changePassword(payload: {
  current_password: string;
  new_password: string;
}): Promise<void> {
  await apiFetch<void>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logout(): void {
  clearTokens();
}
