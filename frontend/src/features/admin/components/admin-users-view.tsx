"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  activateUser,
  deactivateUser,
  listUsers,
  updateUser,
  updateUserRole,
} from "@/services/admin";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";
import type { User, UserRole } from "@/types";

const ROLES: UserRole[] = ["ADMIN", "TRADER", "VIEWER"];

function roleTone(role: string): "ai" | "primary" | "neutral" {
  if (role === "ADMIN") return "ai";
  if (role === "TRADER") return "primary";
  return "neutral";
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function AdminUsersView() {
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((s) => s.user);

  const usersQuery = useQuery({
    queryKey: ["admin", "users"],
    queryFn: () => listUsers({ limit: 200 }),
  });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    void queryClient.invalidateQueries({ queryKey: ["admin", "overview"] });
  };

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: UserRole }) =>
      updateUserRole(userId, role),
    onSuccess: invalidate,
  });

  const statusMutation = useMutation({
    mutationFn: ({ userId, active }: { userId: number; active: boolean }) =>
      active ? activateUser(userId) : deactivateUser(userId),
    onSuccess: invalidate,
  });

  const verifyMutation = useMutation({
    mutationFn: ({ userId, verified }: { userId: number; verified: boolean }) =>
      updateUser(userId, { is_verified: verified }),
    onSuccess: invalidate,
  });

  const users = usersQuery.data ?? [];
  const busyUserId =
    roleMutation.variables?.userId ??
    statusMutation.variables?.userId ??
    verifyMutation.variables?.userId;
  const actionPending =
    roleMutation.isPending || statusMutation.isPending || verifyMutation.isPending;

  const mutationError =
    roleMutation.error || statusMutation.error || verifyMutation.error;
  const errorMessage =
    usersQuery.error instanceof ApiError
      ? usersQuery.error.message
      : usersQuery.error
        ? "Failed to load users"
        : mutationError instanceof ApiError
          ? mutationError.message
          : mutationError instanceof Error
            ? mutationError.message
            : null;

  return (
    <div className="mx-auto max-w-[1200px] space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Administration
          </p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight">Users</h2>
          <p className="mt-1 text-sm text-muted">
            Manage roles, activation, and verification for Athena accounts.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => void usersQuery.refetch()}
          disabled={usersQuery.isFetching}
        >
          <RefreshCw className={`h-3.5 w-3.5 ${usersQuery.isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {errorMessage ? (
        <div className="rounded-sm border border-bearish/30 bg-bearish/10 px-4 py-3 text-sm text-bearish">
          {errorMessage}
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>All users</CardTitle>
          <CardDescription>
            {users.length} account{users.length === 1 ? "" : "s"} loaded
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          {usersQuery.isLoading ? (
            <p className="p-5 text-sm text-muted">Loading users…</p>
          ) : users.length === 0 ? (
            <p className="p-5 text-sm text-muted">No users found.</p>
          ) : (
            <table className="w-full min-w-[860px] text-left text-sm">
              <thead className="border-b border-border bg-panel-elevated/40 text-[11px] uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-5 py-3 font-medium">User</th>
                  <th className="px-5 py-3 font-medium">Role</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Last login</th>
                  <th className="px-5 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <UserRow
                    key={user.id}
                    user={user}
                    isSelf={currentUser?.id === user.id}
                    busy={actionPending && busyUserId === user.id}
                    onRoleChange={(role) =>
                      roleMutation.mutate({ userId: user.id, role })
                    }
                    onToggleActive={() =>
                      statusMutation.mutate({
                        userId: user.id,
                        active: !user.is_active,
                      })
                    }
                    onToggleVerified={() =>
                      verifyMutation.mutate({
                        userId: user.id,
                        verified: !user.is_verified,
                      })
                    }
                  />
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function UserRow({
  user,
  isSelf,
  busy,
  onRoleChange,
  onToggleActive,
  onToggleVerified,
}: {
  user: User;
  isSelf: boolean;
  busy: boolean;
  onRoleChange: (role: UserRole) => void;
  onToggleActive: () => void;
  onToggleVerified: () => void;
}) {
  return (
    <tr className="border-b border-border/70 last:border-0">
      <td className="px-5 py-3 align-top">
        <div className="font-medium">{user.full_name}</div>
        <div className="text-xs text-muted">
          @{user.username} · {user.email}
        </div>
        {isSelf ? (
          <Badge className="mt-1.5" tone="warning">
            You
          </Badge>
        ) : null}
      </td>
      <td className="px-5 py-3 align-top">
        <div className="flex flex-col gap-2">
          <Badge tone={roleTone(user.role)}>{user.role}</Badge>
          <select
            className="h-8 max-w-[140px] rounded-sm border border-border bg-panel px-2 text-xs outline-none focus:border-primary/50"
            value={user.role}
            disabled={busy || (isSelf && user.role === "ADMIN")}
            onChange={(event) => onRoleChange(event.target.value as UserRole)}
          >
            {ROLES.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </div>
      </td>
      <td className="px-5 py-3 align-top">
        <div className="flex flex-wrap gap-1.5">
          <Badge tone={user.is_active ? "bullish" : "bearish"}>
            {user.is_active ? "Active" : "Inactive"}
          </Badge>
          <Badge tone={user.is_verified ? "primary" : "neutral"}>
            {user.is_verified ? "Verified" : "Unverified"}
          </Badge>
        </div>
      </td>
      <td className="px-5 py-3 align-top text-xs text-muted">
        {formatDate(user.last_login)}
      </td>
      <td className="px-5 py-3 align-top">
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant={user.is_active ? "danger" : "bullish"}
            disabled={busy || isSelf}
            onClick={onToggleActive}
          >
            {user.is_active ? "Deactivate" : "Activate"}
          </Button>
          <Button
            size="sm"
            variant="secondary"
            disabled={busy}
            onClick={onToggleVerified}
          >
            {user.is_verified ? "Unverify" : "Verify"}
          </Button>
        </div>
      </td>
    </tr>
  );
}
