"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router";
import { authApi } from "#/api/endpoints";
import { setAuthToken } from "#/api/client";

/* ── Login Page ──────────────────────────────────────────────────────────────
 * Full authentication flow with login/register, token storage,
 * error handling, and redirect to return URL.
 */

export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const returnTo = searchParams.get("returnTo") || "/settings";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");

  const loginMutation = useMutation({
    mutationFn: () => authApi.login(username, password),
    onSuccess: (data) => {
      setAuthToken(data.token);
      navigate(returnTo, { replace: true });
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Login failed. Check your credentials.");
    },
  });

  const registerMutation = useMutation({
    mutationFn: () => authApi.login(username, password),
    onSuccess: (data) => {
      setAuthToken(data.token);
      navigate(returnTo, { replace: true });
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Registration failed. Username may be taken.");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!username.trim() || !password.trim()) {
      setError("Username and password are required.");
      return;
    }
    if (isRegister) {
      registerMutation.mutate();
    } else {
      loginMutation.mutate();
    }
  };

  const isPending = loginMutation.isPending || registerMutation.isPending;

  return (
    <div className="mx-auto flex min-h-[80vh] max-w-md items-center px-6 py-12">
      <div className="w-full">
        <div className="mb-8 text-center">
          <div className="mb-3 inline-flex h-12 w-12 items-center justify-center rounded-xl" style={{ background: "var(--accent)" }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--color-text-primary)" }}>
            {isRegister ? "Create Account" : "Welcome Back"}
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--color-text-tertiary)" }}>
            {isRegister
              ? "Sign up to start building with Wren AI"
              : "Sign in to continue building with Wren AI"}
          </p>
        </div>

        <div className="glass-shell-outer">
          <div className="glass-shell-inner p-6">
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              {error && (
                <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-2.5">
                  <p className="text-xs text-red-400">{error}</p>
                </div>
              )}

              <div>
                <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
                  Username
                </label>
                <input
                  className="input w-full"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder={isRegister ? "Choose a username" : "Your username"}
                  autoFocus
                  disabled={isPending}
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
                  Password
                </label>
                <input
                  className="input w-full"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={isRegister ? "Choose a password" : "Your password"}
                  disabled={isPending}
                />
              </div>

              <button
                type="submit"
                disabled={isPending || !username.trim() || !password.trim()}
                className="accent-button w-full justify-center text-xs"
              >
                {isPending ? (
                  <span className="flex items-center gap-2">
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    {isRegister ? "Creating account..." : "Signing in..."}
                  </span>
                ) : isRegister ? (
                  "Create Account"
                ) : (
                  "Sign In"
                )}
              </button>

              <p className="pt-2 text-center text-xs" style={{ color: "var(--color-text-tertiary)" }}>
                {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
                <button
                  type="button"
                  onClick={() => {
                    setIsRegister(!isRegister);
                    setError("");
                  }}
                  className="font-medium underline-offset-2 hover:underline"
                  style={{ color: "var(--accent)" }}
                >
                  {isRegister ? "Sign in" : "Create one"}
                </button>
              </p>
            </form>

            {/* Default credentials hint */}
            {!isRegister && (
              <div className="mt-4 rounded-lg bg-white/[0.03] px-4 py-2.5">
                <p className="text-[10px] leading-relaxed" style={{ color: "var(--color-text-tertiary)" }}>
                  <strong>Demo:</strong> admin / admin
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
