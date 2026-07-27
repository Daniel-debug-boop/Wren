import { Outlet, Link, useLocation } from "react-router";

export default function RootLayout() {
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <div
      className="flex min-h-screen flex-col"
      style={{ background: "var(--color-surface-base)" }}
    >
      {!isHome && (
        <header
          className="flex h-12 items-center justify-between border-b px-5"
          style={{
            background: "color-mix(in srgb, var(--surface) 85%, transparent)",
            borderColor: "var(--border)",
            backdropFilter: "blur(12px)",
          }}
        >
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="flex items-center gap-2.5"
            >
              <div
                className="flex h-7 w-7 items-center justify-center rounded-md"
                style={{
                  background: "linear-gradient(135deg, var(--accent), var(--accent-hover))",
                }}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2 2 7l10 5 10-5-10-5Z" />
                  <path d="m2 17 10 5 10-5" />
                  <path d="m2 12 10 5 10-5" />
                </svg>
              </div>
              <span className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
                Wren
              </span>
            </Link>
          </div>

          <nav className="flex items-center gap-1">
            <Link
              to="/settings"
              className="press flex h-8 items-center gap-1.5 rounded-md px-3 text-xs font-medium transition-all"
              style={{ color: "var(--color-text-tertiary)" }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
              Settings
            </Link>
          </nav>
        </header>
      )}

      <main id="main" className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
