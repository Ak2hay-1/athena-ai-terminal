import { config } from "@/lib/config";
import type { TokenResponse } from "@/types";

const ACCESS_KEY = "athena_access_token";
const REFRESH_KEY = "athena_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(tokens: TokenResponse): void {
  localStorage.setItem(ACCESS_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  const response = await fetch(`${config.apiUrl}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });

  if (!response.ok) {
    clearTokens();
    return null;
  }

  const tokens = (await response.json()) as TokenResponse;
  setTokens(tokens);
  return tokens.access_token;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);

  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  let token = getAccessToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response = await fetch(`${config.apiUrl}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && getRefreshToken()) {
    token = await refreshAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
      response = await fetch(`${config.apiUrl}${path}`, {
        ...options,
        headers,
      });
    }
  }

  if (!response.ok) {
    const message = await response.text();
    throw new ApiError(response.status, message || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
