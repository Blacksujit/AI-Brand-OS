import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url: string | null;
  is_active: boolean;
  is_onboarded: boolean;
  last_login_at: string | null;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isOnboarded: boolean;
  setAuth: (access: string, refresh: string, user?: User) => void;
  clearAuth: () => void;
  setUser: (user: User) => void;
  setOnboarded: (v: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isOnboarded: false,
      setAuth: (access, refresh, user) =>
        set({ accessToken: access, refreshToken: refresh, user: user ?? null }),
      clearAuth: () =>
        set({ user: null, accessToken: null, refreshToken: null, isOnboarded: false }),
      setUser: (user) => set({ user }),
      setOnboarded: (v) => set({ isOnboarded: v }),
    }),
    {
      name: "brandos-auth-store",
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        isOnboarded: s.isOnboarded,
      }),
    }
  )
);