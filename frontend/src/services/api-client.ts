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
  // #region agent log
  fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'77d2e9'},body:JSON.stringify({sessionId:'77d2e9',runId:'pre-fix',hypothesisId:'C',location:'api-client.ts:clearTokens',message:'clearTokens called',data:{stack:(new Error()).stack?.split('\n').slice(0,6)},timestamp:Date.now()})}).catch(()=>{});
  // #endregion
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) {
    // #region agent log
    fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'77d2e9'},body:JSON.stringify({sessionId:'77d2e9',runId:'pre-fix',hypothesisId:'C',location:'api-client.ts:refreshAccessToken',message:'refresh skipped — no refresh token',data:{},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    return null;
  }

  const response = await fetch(`${config.apiUrl}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });

  if (!response.ok) {
    // #region agent log
    fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'77d2e9'},body:JSON.stringify({sessionId:'77d2e9',runId:'pre-fix',hypothesisId:'C',location:'api-client.ts:refreshAccessToken',message:'refresh failed — clearing tokens',data:{status:response.status},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    clearTokens();
    return null;
  }

  const tokens = (await response.json()) as TokenResponse;
  setTokens(tokens);
  // #region agent log
  fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'77d2e9'},body:JSON.stringify({sessionId:'77d2e9',runId:'pre-fix',hypothesisId:'C',location:'api-client.ts:refreshAccessToken',message:'refresh succeeded',data:{hasAccess:Boolean(tokens?.access_token)},timestamp:Date.now()})}).catch(()=>{});
  // #endregion
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

  const url = `${config.apiUrl}${path}`;

  // #region agent log
  fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'77d2e9'},body:JSON.stringify({sessionId:'77d2e9',runId:'pre-fix',hypothesisId:'A',location:'api-client.ts:apiFetch:entry',message:'apiFetch entry',data:{path,method:options.method??'GET',hasAccessToken:Boolean(token),accessLen:token?.length??0,hasRefreshToken:Boolean(getRefreshToken()),hasAuthHeader:headers.has('Authorization'),apiUrl:config.apiUrl},timestamp:Date.now()})}).catch(()=>{});
  // #endregion

  let response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401 && getRefreshToken()) {
    // #region agent log
    fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'77d2e9'},body:JSON.stringify({sessionId:'77d2e9',runId:'pre-fix',hypothesisId:'C',location:'api-client.ts:apiFetch:401',message:'got 401 — attempting refresh',data:{path,hadAuthHeader:headers.has('Authorization')},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    token = await refreshAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
      response = await fetch(url, {
        ...options,
        headers,
      });
    }
  }

  if (!response.ok) {
    const message = await response.text();
    let detail = message || `Request failed: ${response.status}`;
    try {
      const parsed = JSON.parse(message) as {
        detail?: unknown;
        error?: unknown;
      };
      if (typeof parsed.detail === "string") {
        detail = parsed.detail;
      } else if (typeof parsed.error === "string") {
        detail = parsed.error;
      } else if (Array.isArray(parsed.detail)) {
        detail = parsed.detail
          .map((item) =>
            typeof item === "object" && item && "msg" in item
              ? String((item as { msg: unknown }).msg)
              : String(item),
          )
          .join("; ");
      }
    } catch {
      /* keep raw text */
    }
    // #region agent log
    fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'77d2e9'},body:JSON.stringify({sessionId:'77d2e9',runId:'pre-fix',hypothesisId:'A',location:'api-client.ts:apiFetch:error',message:'apiFetch error response',data:{path,status:response.status,detail:detail.slice(0,200),hasAccessAfter:Boolean(getAccessToken()),hasRefreshAfter:Boolean(getRefreshToken()),hasAuthHeader:headers.has('Authorization')},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
