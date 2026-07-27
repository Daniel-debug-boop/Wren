/* ── Login Page ──────────────────────────────────────────────────────────────
 * Demo info page. No auth required — Wren is free to use.
 * Enterprise tier handles authentication server-side.
 */

import { Link } from "react-router";

export default function LoginPage() {
  return (
    <div className="mx-auto flex min-h-[80vh] max-w-md items-center px-6 py-12">
      <div className="w-full">
        <div className="mb-8 text-center">
          <div className="mb-3 inline-flex h-12 w-12 items-center justify-center rounded-xl" style={{ background: "var(--accent)" }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            Wren is Free
          </h1>
          <p className="mt-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
            No account needed. No login required.
            <br />
            Just drop in your API key and start building.
          </p>
        </div>

        <div className="card p-6">
          <div className="space-y-4">
            <div className="rounded-lg p-4" style={{ background: "var(--accent-subtle)", border: "1px solid rgba(245,158,11,0.12)" }}>
              <h3 className="text-sm font-semibold mb-1 flex items-center gap-2" style={{ color: "var(--accent)" }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
                Free & Open Source
              </h3>
              <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                The community edition is completely free with no authentication required.
                Enterprise features (SSO, audit logs, dedicated agents) require a license.
              </p>
            </div>

            <div className="rounded-lg p-4" style={{ background: "var(--accent-subtle)", border: "1px solid rgba(245,158,11,0.12)" }}>
              <h3 className="text-sm font-semibold mb-1 flex items-center gap-2" style={{ color: "var(--accent)" }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg>
                Quick Start
              </h3>
              <ol className="text-xs space-y-1.5 mt-2" style={{ color: "var(--text-secondary)" }}>
                <li>1. Go to <strong>Settings</strong> to configure your LLM provider</li>
                <li>2. Add your OpenRouter (or other) API key</li>
                <li>3. Use <strong>Generate</strong> for AI-powered project generation</li>
                <li>4. Use <strong>Chat</strong> for interactive assistance</li>
              </ol>
            </div>

            <Link to="/settings" className="btn-primary w-full justify-center text-xs">
              Go to Settings
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
