/**
 * Zustand auth store.
 *
 * Why Zustand over Redux?
 * - Zero boilerplate. No actions, reducers, or selectors to write.
 * - Works perfectly with TypeScript inference.
 * - The `persist` middleware (used below) handles localStorage serialisation.
 *
 * What's stored:
 *   - user: the current user object (role, email, name)
 *   - accessToken: short-lived JWT (15 min)
 *   - refreshToken: long-lived JWT (7 days)
 *
 * Note: in a production app, the refresh token should be an httpOnly cookie.
 * For Phase 1, both tokens are stored in Zustand (in-memory across the session).
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      setAuth: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken }),

      setTokens: (accessToken, refreshToken) =>
        set({ accessToken, refreshToken }),

      logout: () => set({ user: null, accessToken: null, refreshToken: null }),

      isAuthenticated: () => get().accessToken !== null,
    }),
    {
      name: "classpulse-auth",
      // Only persist the refresh token + user to sessionStorage.
      // Access token is re-acquired on page load via the refresh token.
      partialize: (state) => ({
        user: state.user,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
