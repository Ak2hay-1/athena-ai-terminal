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
    if (!getAccessToken()) {
      set({ user: null, loading: false, initialized: true });
      return;
    }

    try {
      const user = await getMe();
      set({ user, loading: false, initialized: true });
    } catch {
      clearTokens();
      set({ user: null, loading: false, initialized: true });
    }
  },
  login: async (username, password) => {
    await loginRequest(username, password);
    const user = await getMe();
    set({ user, loading: false, initialized: true });
  },
  setUser: (user) => set({ user }),
  logout: () => {
    logoutRequest();
    set({ user: null });
  },
}));
