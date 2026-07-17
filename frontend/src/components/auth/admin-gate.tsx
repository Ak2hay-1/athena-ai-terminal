"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";

export function AdminGate({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const loading = useAuthStore((s) => s.loading);
  const router = useRouter();

  const isAdmin = user?.role === "ADMIN";

  useEffect(() => {
    if (!loading && user && !isAdmin) {
      router.replace("/");
    }
  }, [isAdmin, loading, router, user]);

  if (loading || !user) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-muted">
        Checking admin access…
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-muted">
        Redirecting…
      </div>
    );
  }

  return <>{children}</>;
}
