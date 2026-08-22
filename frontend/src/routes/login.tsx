/* ── Login Page ──────────────────────────────────────────────────────────────
 * Demo info page. No auth required — Wren is free to use.
 * Enterprise tier handles authentication server-side.
 */

import { Link } from "react-router";

export default function LoginPage() {
  return (
    <div className="mx-auto flex min-h-[80vh] max-w-md items-center px-4 py-12 md:px-6">
      <div className="w-full animate-fade-up">
        <div className="mb-8 text-center">
          <div
            className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl shadow-lg"
            style={{
              background:
                "linear-gradient(135deg, var(--accent), var(--accent-hover))",
            }}
          >
            <svg
              width="26"
              height="26"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#fffaf7"
              strokeWidth="2.5"
              strokeLinecap="round"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1
            className="font-display text-2xl font-semibold tracking-tight"
            style={{ color: "var(--text-primary)" }}
          >
            Wren is Free
          </h1>
          <p
            className="mt-2.5 text-sm leading-relaxed"
            style={{ color: "var(--text-tertiary)" }}
          >
            No account needed. No login required.
            <br />
            Just drop in your API key and start building.
          </p>
        </div>

        <div className="card p-6 md:p-7">
          <div className="space-y-4">
            <div
              className="rounded-xl border p-4"
              style={{
                background: "var(--accent-subtle)",
                borderColor: "rgba(217,119,87,0.18)",
              }}
            >
              <h3
                className="mb-1 flex items-center gap-2 text-sm font-semibold"
                style={{ color: "var(--accent-strong)" }}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                >
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
                Free &amp; Open Source
              </h3>
              <p
                className="text-xs leading-relaxed"
                style={{ color: "var(--text-secondary)" }}
              >
                The community edition is completely free with no authentication
                required. Enterprise features (SSO, audit logs, dedicated
                agents) require a license.
              </p>
            </div>

            <div
              className="rounded-xl border p-4"
              style={{
                background: "var(--bg-surface)",
                borderColor: "var(--border)",
              }}
            >
              <h3
                className="flex items-center gap-2 text-sm font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="var(--accent-strong)"
                  strokeWidth="2"
                  strokeLinecap="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 16v-4M12 8h.01" />
                </svg>
                Quick Start
              </h3>
              <ol
                className="mt-3 space-y-2 text-xs leading-relaxed"
                style={{ color: "var(--text-secondary)" }}
              >
                <li className="flex gap-2">
                  <span
                    className="font-display shrink-0 font-semibold"
                    style={{ color: "var(--accent-strong)" }}
                  >
                    1.
                  </span>
                  Go to <strong>Settings</strong> to configure your LLM provider
                </li>
                <li className="flex gap-2">
                  <span
                    className="font-display shrink-0 font-semibold"
                    style={{ color: "var(--accent-strong)" }}
                  >
                    2.
                  </span>
                  Add your OpenRouter (or other) API key
                </li>
                <li className="flex gap-2">
                  <span
                    className="font-display shrink-0 font-semibold"
                    style={{ color: "var(--accent-strong)" }}
                  >
                    3.
                  </span>
                  Use <strong>Generate</strong> for AI-powered project
                  generation
                </li>
                <li className="flex gap-2">
                  <span
                    className="font-display shrink-0 font-semibold"
                    style={{ color: "var(--accent-strong)" }}
                  >
                    4.
                  </span>
                  Use <strong>Chat</strong> for interactive assistance
                </li>
              </ol>
            </div>

            <Link
              to="/settings"
              className="btn-primary w-full justify-center text-xs"
            >
              Go to Settings
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
