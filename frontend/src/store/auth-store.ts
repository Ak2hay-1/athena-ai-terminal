"use client";

import { create } from "zustand";
import { clearTokens, getAccessToken } from "@/services/api-client";
import { getMe, login as loginRequest, logout as logoutRequest } from "@/services/auth";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  initialized: boolean;
  initialize: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: true,
  initialized: false,
  initialize: async () => {
    const access = getAccessToken();
    // #region agent log
    fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'2d949e'},body:JSON.stringify({sessionId:'2d949e',runId:'login-verify',hypothesisId:'D',location:'auth-store.ts:initialize',message:'auth initialize',data:{hasAccess:Boolean(access),accessLen:access?.length??0},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    if (!access) {
      set({ user: null, loading: false, initialized: true });
      return;
    }

    try {
      const user = await getMe();
      // #region agent log
      fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'2d949e'},body:JSON.stringify({sessionId:'2d949e',runId:'login-verify',hypothesisId:'D',location:'auth-store.ts:initialize:ok',message:'auth initialize getMe ok',data:{userId:user?.id??null,username:user?.username??null},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      set({ user, loading: false, initialized: true });
    } catch {
      clearTokens();
      set({ user: null, loading: false, initialized: true });
    }
  },
  login: async (username, password) => {
    try {
      await loginRequest(username, password);
    } catch (err) {
      // #region agent log
      fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'2d949e'},body:JSON.stringify({sessionId:'2d949e',runId:'login-verify',hypothesisId:'E',location:'auth-store.ts:login:loginRequest-fail',message:'loginRequest failed',data:{err:err instanceof Error?err.message:String(err)},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      throw err;
    }
    try {
      const user = await getMe();
      // #region agent log
      fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'2d949e'},body:JSON.stringify({sessionId:'2d949e',runId:'login-verify',hypothesisId:'A',location:'auth-store.ts:login:getMe-ok',message:'getMe succeeded after login',data:{userId:user?.id??null,username:user?.username??null,hasAccess:Boolean(getAccessToken())},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      set({ user, loading: false, initialized: true });
    } catch (err) {
      // #region agent log
      fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'2d949e'},body:JSON.stringify({sessionId:'2d949e',runId:'login-verify',hypothesisId:'A',location:'auth-store.ts:login:getMe-fail',message:'getMe failed after login',data:{err:err instanceof Error?err.message:String(err)},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      throw err;
    }
  },
  setUser: (user) => set({ user }),
  logout: () => {
    logoutRequest();
    set({ user: null });
  },
}));
