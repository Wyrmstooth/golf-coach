import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserOut } from "../api/auth";

interface AuthState {
  user: UserOut | null;
  token: string | null;
  setAuth: (user: UserOut, token: string) => void;
  setUser: (user: UserOut) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (user, token) => set({ user, token }),
      setUser: (user) => set({ user }),
      logout: () => set({ user: null, token: null }),
    }),
    {
      name: "golf-auth",
    }
  )
);
