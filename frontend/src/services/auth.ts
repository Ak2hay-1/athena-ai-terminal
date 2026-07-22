import { apiFetch, clearTokens, setTokens } from "@/services/api-client";
import type { TokenResponse, User } from "@/types";
import { config } from "@/lib/config";

export async function login(
  username: string,
  password: string,
): Promise<TokenResponse> {
  let response: Response;
  const loginUrl = `${config.apiUrl}/auth/login`;
  // #region agent log
  fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'2d949e'},body:JSON.stringify({sessionId:'2d949e',runId:'login-verify',hypothesisId:'A',location:'auth.ts:login:start',message:'login request start',data:{loginUrl,apiUrl:config.apiUrl,origin:typeof window!=='undefined'?window.location.origin:null,usernameLen:username.length,passwordLen:password.length},timestamp:Date.now()})}).catch(()=>{});
  // #endregion
  try {
    response = await fetch(loginUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
      signal: AbortSignal.timeout(15_000),
    });
  } catch (err) {
    // #region agent log
    fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'2d949e'},body:JSON.stringify({sessionId:'2d949e',runId:'login-verify',hypothesisId:'A',location:'auth.ts:login:network',message:'login fetch threw (network/CORS/timeout)',data:{loginUrl,err:err instanceof Error?err.message:String(err),name:err instanceof Error?err.name:null},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    throw new Error("Backend unreachable");
  }

  if (!response.ok) {
    let bodyPreview = "";
    try {
      bodyPreview = (await response.clone().text()).slice(0, 300);
    } catch {
      bodyPreview = "<unreadable>";
    }
    // #region agent log
    fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'2d949e'},body:JSON.stringify({sessionId:'2d949e',runId:'login-verify',hypothesisId:'D',location:'auth.ts:login:http-error',message:'login HTTP not ok',data:{status:response.status,statusText:response.statusText,bodyPreview},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    throw new Error("Invalid credentials");
  }

  const tokens = (await response.json()) as TokenResponse;
  // #region agent log
  fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'2d949e'},body:JSON.stringify({sessionId:'2d949e',runId:'login-verify',hypothesisId:'A',location:'auth.ts:login:ok',message:'login tokens received',data:{hasAccess:Boolean(tokens?.access_token),hasRefresh:Boolean(tokens?.refresh_token),tokenType:tokens?.token_type??null},timestamp:Date.now()})}).catch(()=>{});
  // #endregion
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
