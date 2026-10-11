
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { api, getToken, setToken, type User } from "./api";
import { AuthContext, type AuthContextValue } from "./auth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      if (!getToken()) {
        setInitializing(false);
        return;
      }

      try {
        const currentUser = await api.me();
        if (active) {
          setUser(currentUser);
        }
      } catch {
        setToken(null);
      } finally {
        if (active) {
          setInitializing(false);
        }
      }
    }

    restoreSession();

    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      initializing,
      async login(email, password) {
        const response = await api.login(email, password);
        setToken(response.access_token);
        setUser(response.user);
      },
      async register(name, email, password) {
        const response = await api.register(name, email, password);
        setToken(response.access_token);
        setUser(response.user);
      },
      logout() {
        setToken(null);
        setUser(null);
      },
    }),
    [user, initializing]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
