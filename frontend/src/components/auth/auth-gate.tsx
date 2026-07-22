"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getAccessToken, getRefreshToken } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const loading = useAuthStore((s) => s.loading);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // #region agent log
    fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'77d2e9'},body:JSON.stringify({sessionId:'77d2e9',runId:'pre-fix',hypothesisId:'D',location:'auth-gate.tsx:effect',message:'AuthGate state',data:{loading,hasUser:Boolean(user),userId:user?.id??null,hasAccess:Boolean(getAccessToken()),hasRefresh:Boolean(getRefreshToken()),willRenderChildren:Boolean(!loading && user),pathname,origin:typeof window!=='undefined'?window.location.origin:null},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    if (!loading && !user) {
      router.replace(`/login?next=${encodeURIComponent(pathname || "/")}`);
    }
  }, [loading, pathname, router, user]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted">
        Checking session…
      </div>
    );
  }

  return <>{children}</>;
}
