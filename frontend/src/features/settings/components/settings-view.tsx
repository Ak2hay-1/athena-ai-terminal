"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MARKET_SYMBOLS, TIMEFRAMES } from "@/constants/markets";
import { AutoTradeFiltersForm } from "@/features/trading/components/auto-trade-filters-form";
import { changePassword, updateMe } from "@/services/auth";
import {
  DEFAULT_AUTO_TRADE,
  PREFERENCES_QUERY_KEY,
  autoTradeFromPreferences,
  getPreferences,
  updatePreferences,
  type AutoTradeFilters,
} from "@/services/preferences";
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
  const queryClient = useQueryClient();

  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [prefs, setPrefs] = useState<LocalPrefs>(loadPrefs);
  const [autoTrade, setAutoTrade] =
    useState<AutoTradeFilters>(DEFAULT_AUTO_TRADE);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const serverPrefsQuery = useQuery({
    queryKey: PREFERENCES_QUERY_KEY,
    queryFn: getPreferences,
    enabled: Boolean(user),
    staleTime: 30_000,
  });

  useEffect(() => {
    setFullName(user?.full_name ?? "");
    setEmail(user?.email ?? "");
  }, [user]);

  useEffect(() => {
    if (serverPrefsQuery.data) {
      setAutoTrade(autoTradeFromPreferences(serverPrefsQuery.data));
    }
  }, [serverPrefsQuery.data]);

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

  const autoTradeMutation = useMutation({
    mutationFn: () =>
      updatePreferences({
        auto_trade_enabled: autoTrade.auto_trade_enabled,
        auto_trade_symbols: autoTrade.auto_trade_symbols,
        auto_trade_timeframes: autoTrade.auto_trade_timeframes,
        auto_trade_min_confidence: autoTrade.auto_trade_min_confidence,
        auto_trade_min_confluence: autoTrade.auto_trade_min_confluence,
        auto_trade_min_rr: autoTrade.auto_trade_min_rr,
        auto_trade_volume: autoTrade.auto_trade_volume,
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(PREFERENCES_QUERY_KEY, data);
      setAutoTrade(autoTradeFromPreferences(data));
      setStatus("Auto trade settings saved.");
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message || "Failed to save auto trade settings.");
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
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>Auto Trade</CardTitle>
          <Badge tone={autoTrade.auto_trade_enabled ? "bullish" : "default"}>
            {autoTrade.auto_trade_enabled ? "ON" : "OFF"}
          </Badge>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-3"
            onSubmit={(event) => {
              event.preventDefault();
              autoTradeMutation.mutate();
            }}
          >
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="accent-primary"
                checked={autoTrade.auto_trade_enabled}
                onChange={(event) =>
                  setAutoTrade((prev) => ({
                    ...prev,
                    auto_trade_enabled: event.target.checked,
                  }))
                }
              />
              Enable auto trading — matching Athena signals place MT5 orders directly
            </label>
            <AutoTradeFiltersForm value={autoTrade} onChange={setAutoTrade} />
            <Button
              type="submit"
              variant="secondary"
              disabled={autoTradeMutation.isPending || serverPrefsQuery.isLoading}
            >
              {autoTradeMutation.isPending
                ? "Saving…"
                : "Save auto trade settings"}
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
