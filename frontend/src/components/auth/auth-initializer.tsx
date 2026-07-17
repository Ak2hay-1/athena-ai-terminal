"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/auth-store";

export function AuthInitializer({ children }: { children: React.ReactNode }) {
  const initialize = useAuthStore((s) => s.initialize);
  const initialized = useAuthStore((s) => s.initialized);

  useEffect(() => {
    void initialize();
  }, [initialize]);

  if (!initialized) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted">
        Connecting to Athena…
      </div>
    );
  }

  return <>{children}</>;
}
