"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MARKET_SYMBOLS, TIMEFRAMES } from "@/constants/markets";
import { changePassword, updateMe } from "@/services/auth";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";
import { useUiStore } from "@/store/ui-store";

const PREFS_KEY = "athena.settings.prefs";

type LocalPrefs = {
  defaultSymbol: string;
  defaultTimeframe: string;
  showAssistant: boolean;
  riskPercent: number;
};

function loadPrefs(): LocalPrefs {
  if (typeof window === "undefined") {
    return {
      defaultSymbol: "XAUUSD",
      defaultTimeframe: "M5",
      showAssistant: true,
      riskPercent: 1,
    };
  }
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    if (!raw) {
      return {
        defaultSymbol: "XAUUSD",
        defaultTimeframe: "M5",
        showAssistant: true,
        riskPercent: 1,
      };
    }
    return { ...JSON.parse(raw) } as LocalPrefs;
  } catch {
    return {
      defaultSymbol: "XAUUSD",
      defaultTimeframe: "M5",
      showAssistant: true,
      riskPercent: 1,
    };
  }
}

export function SettingsView() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const logout = useAuthStore((s) => s.logout);
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);
  const setRightPanel = useUiStore((s) => s.setRightPanel);

  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [prefs, setPrefs] = useState<LocalPrefs>(loadPrefs);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setFullName(user?.full_name ?? "");
    setEmail(user?.email ?? "");
  }, [user]);

  const profileMutation = useMutation({
    mutationFn: () => updateMe({ full_name: fullName, email }),
    onSuccess: (updated) => {
      setUser(updated);
      setStatus("Profile updated.");
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message || "Failed to update profile.");
      setStatus(null);
    },
  });

  const passwordMutation = useMutation({
    mutationFn: () =>
      changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setStatus("Password changed.");
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message || "Failed to change password.");
      setStatus(null);
    },
  });

  function savePrefs(event: FormEvent) {
    event.preventDefault();
    localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
    setSymbol(prefs.defaultSymbol);
    setTimeframe(prefs.defaultTimeframe);
    setRightPanel(prefs.showAssistant ? "assistant" : "hidden");
    setStatus("Workspace preferences saved.");
    setError(null);
  }

  return (
    <div className="mx-auto max-w-[900px] space-y-4">
      <div className="border-b border-border pb-4">
        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
          Settings
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">Workspace</h1>
        <p className="mt-1 text-sm text-muted">
          Profile, risk defaults, and assistant behavior
        </p>
      </div>

      {status ? (
        <div className="rounded-sm border border-bullish/30 bg-bullish/10 px-3 py-2 text-sm text-bullish">
          {status}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-sm border border-bearish/30 bg-bearish/10 px-3 py-2 text-sm text-bearish">
          {error}
        </div>
      ) : null}

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>Account</CardTitle>
          <Badge tone="primary">{user?.role ?? "—"}</Badge>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-3"
            onSubmit={(event) => {
              event.preventDefault();
              profileMutation.mutate();
            }}
          >
            <label className="block space-y-1.5 text-sm">
              <span className="text-muted">Username</span>
              <input
                value={user?.username ?? ""}
                disabled
                className="h-9 w-full rounded-sm border border-border bg-background/40 px-3 font-mono text-sm opacity-70"
              />
            </label>
            <label className="block space-y-1.5 text-sm">
              <span className="text-muted">Full name</span>
              <input
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                className="h-9 w-full rounded-sm border border-border bg-panel px-3 text-sm outline-none focus:border-primary/50"
              />
            </label>
            <label className="block space-y-1.5 text-sm">
              <span className="text-muted">Email</span>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="h-9 w-full rounded-sm border border-border bg-panel px-3 text-sm outline-none focus:border-primary/50"
              />
            </label>
            <Button type="submit" disabled={profileMutation.isPending}>
              {profileMutation.isPending ? "Saving…" : "Save profile"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Password</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-3"
            onSubmit={(event) => {
              event.preventDefault();
              passwordMutation.mutate();
            }}
          >
            <label className="block space-y-1.5 text-sm">
              <span className="text-muted">Current password</span>
              <input
                type="password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                className="h-9 w-full rounded-sm border border-border bg-panel px-3 text-sm outline-none focus:border-primary/50"
                required
              />
            </label>
            <label className="block space-y-1.5 text-sm">
              <span className="text-muted">New password</span>
              <input
                type="password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                minLength={8}
                className="h-9 w-full rounded-sm border border-border bg-panel px-3 text-sm outline-none focus:border-primary/50"
                required
              />
            </label>
            <Button
              type="submit"
              variant="secondary"
              disabled={passwordMutation.isPending}
            >
              {passwordMutation.isPending ? "Updating…" : "Change password"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Trading preferences</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-3" onSubmit={savePrefs}>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block space-y-1.5 text-sm">
                <span className="text-muted">Default symbol</span>
                <select
                  value={prefs.defaultSymbol}
                  onChange={(event) =>
                    setPrefs((prev) => ({ ...prev, defaultSymbol: event.target.value }))
                  }
                  className="h-9 w-full rounded-sm border border-border bg-panel px-3 font-mono text-sm outline-none focus:border-primary/50"
                >
                  {MARKET_SYMBOLS.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block space-y-1.5 text-sm">
                <span className="text-muted">Default timeframe</span>
                <select
                  value={prefs.defaultTimeframe}
                  onChange={(event) =>
                    setPrefs((prev) => ({
                      ...prev,
                      defaultTimeframe: event.target.value,
                    }))
                  }
                  className="h-9 w-full rounded-sm border border-border bg-panel px-3 font-mono text-sm outline-none focus:border-primary/50"
                >
                  {TIMEFRAMES.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className="block space-y-1.5 text-sm">
              <span className="text-muted">Default risk %</span>
              <input
                type="number"
                min={0.1}
                max={5}
                step={0.1}
                value={prefs.riskPercent}
                onChange={(event) =>
                  setPrefs((prev) => ({
                    ...prev,
                    riskPercent: Number(event.target.value),
                  }))
                }
                className="h-9 w-full rounded-sm border border-border bg-panel px-3 font-mono text-sm outline-none focus:border-primary/50"
              />
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={prefs.showAssistant}
                onChange={(event) =>
                  setPrefs((prev) => ({
                    ...prev,
                    showAssistant: event.target.checked,
                  }))
                }
                className="accent-primary"
              />
              Show AI assistant panel by default
            </label>
            <Button type="submit" variant="secondary">
              Save preferences
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Session</CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="danger" onClick={() => logout()}>
            Sign out
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
