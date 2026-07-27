"use client";

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";
import { useNavigate } from "react-router";
import { setAuthToken, getAuthToken } from "#/api/client";
import { authApi } from "#/api/endpoints";

/* ── Auth Context ────────────────────────────────────────────────────────────
 * Provides authentication state, login/logout functions, and token persistence.
 */

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  username: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore token from session on mount
  useEffect(() => {
    const saved = sessionStorage.getItem("wren_auth_token");
    const savedUser = sessionStorage.getItem("wren_username");
    if (saved) {
      setToken(saved);
      setAuthToken(saved);
      setUsername(savedUser);
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const result = await authApi.login(username, password);
    setToken(result.token);
    setUsername(result.user.username);
    setAuthToken(result.token);
    sessionStorage.setItem("wren_auth_token", result.token);
    sessionStorage.setItem("wren_username", result.user.username);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {}
    setToken(null);
    setUsername(null);
    setAuthToken(null);
    sessionStorage.removeItem("wren_auth_token");
    sessionStorage.removeItem("wren_username");
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!token,
        token,
        username,
        login,
        logout,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}

/* ── Auth Guard ──────────────────────────────────────────────────────────────
 * Wraps routes that require authentication. Redirects to login if not authed.
 */

export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate("/login", { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex items-center gap-2">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
          <span className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>Loading...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return <>{children}</>;
}
