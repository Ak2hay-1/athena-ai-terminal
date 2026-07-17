"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth-store";

export function LoginForm() {
  const login = useAuthStore((s) => s.login);
  const router = useRouter();
  const searchParams = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await login(username, password);
      const next = searchParams.get("next") || "/";
      router.replace(next);
    } catch {
      setError("Invalid credentials or backend unreachable.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
        Athena
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">Sign in</h1>
      <p className="mt-2 text-sm text-muted">
        Live market intelligence requires an authenticated session.
      </p>

      <form
        onSubmit={onSubmit}
        className="mt-8 space-y-4 rounded-2xl border border-border bg-panel p-6 shadow-lg shadow-black/20"
      >
        <label className="block space-y-1.5">
          <span className="text-xs font-medium text-muted">Username</span>
          <input
            className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            required
          />
        </label>
        <label className="block space-y-1.5">
          <span className="text-xs font-medium text-muted">Password</span>
          <input
            type="password"
            className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error ? <p className="text-sm text-bearish">{error}</p> : null}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <p className="mt-4 text-center text-sm text-muted">
        No account?{" "}
        <Link href="/register" className="text-primary hover:underline">
          Register
        </Link>
      </p>
    </div>
  );
}
