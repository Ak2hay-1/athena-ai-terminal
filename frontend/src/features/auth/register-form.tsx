"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { register } from "@/services/auth";
import { useAuthStore } from "@/store/auth-store";

export function RegisterForm() {
  const login = useAuthStore((s) => s.login);
  const router = useRouter();
  const [form, setForm] = useState({
    username: "",
    email: "",
    full_name: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await register(form);
      await login(form.username, form.password);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
        Athena
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">Create account</h1>
      <p className="mt-2 text-sm text-muted">
        Register to stream live recommendations and market context.
      </p>

      <form
        onSubmit={onSubmit}
        className="mt-8 space-y-3 rounded-2xl border border-border bg-panel p-6"
      >
        {(
          [
            ["username", "Username"],
            ["email", "Email"],
            ["full_name", "Full name"],
            ["password", "Password"],
          ] as const
        ).map(([key, label]) => (
          <label key={key} className="block space-y-1.5">
            <span className="text-xs font-medium text-muted">{label}</span>
            <input
              type={key === "password" ? "password" : key === "email" ? "email" : "text"}
              className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
              value={form[key]}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, [key]: event.target.value }))
              }
              required
            />
          </label>
        ))}
        {error ? <p className="text-sm text-bearish">{error}</p> : null}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Creating…" : "Create account"}
        </Button>
      </form>

      <p className="mt-4 text-center text-sm text-muted">
        Already have an account?{" "}
        <Link href="/login" className="text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
