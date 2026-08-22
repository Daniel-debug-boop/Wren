import { useState, useEffect } from "react";
import { Outlet, Link, useLocation } from "react-router";

/* ── Navigation Items ──────────────────────────────────────────────────────── */

const NAV_ITEMS = [
  {
    to: "/",
    label: "Home",
    icon: (
      <svg
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    to: "/generation",
    label: "Generate",
    icon: (
      <svg
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    ),
  },
  {
    to: "/conversation",
    label: "Chat",
    icon: (
      <svg
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    to: "/settings",
    label: "Settings",
    icon: (
      <svg
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.51 1.51 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    ),
  },
  {
    to: "/api-keys",
    label: "API Keys",
    icon: (
      <svg
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
      </svg>
    ),
  },
  {
    to: "/skills",
    label: "Skills",
    icon: (
      <svg
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    ),
  },
];

/* ── Layout ── */

export default function RootLayout() {
  const location = useLocation();
  const isHome = location.pathname === "/";
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  /* Close the drawer whenever the route changes */
  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  /* Close the drawer on Escape */
  useEffect(() => {
    if (!mobileNavOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileNavOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobileNavOpen]);

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-deep)" }}>
      {/* Sidebar — only for internal pages */}
      {!isHome && (
        <>
          {/* Mobile top bar */}
          <header
            className="glass fixed inset-x-0 top-0 z-40 flex h-12 items-center gap-3 border-b px-3 lg:hidden"
            style={{ borderColor: "var(--border)" }}
          >
            <button
              type="button"
              onClick={() => setMobileNavOpen((v) => !v)}
              aria-expanded={mobileNavOpen}
              aria-label="Toggle navigation"
              className="flex h-8 w-8 items-center justify-center rounded-md transition-colors duration-200 ease-out hover:bg-black/5"
              style={{ color: "var(--text-primary)" }}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
              >
                {mobileNavOpen ? (
                  <path d="M18 6L6 18M6 6l12 12" />
                ) : (
                  <>
                    <line x1="4" y1="7" x2="20" y2="7" />
                    <line x1="4" y1="12" x2="20" y2="12" />
                    <line x1="4" y1="17" x2="20" y2="17" />
                  </>
                )}
              </svg>
            </button>
            <div
              className="flex h-6 w-6 items-center justify-center rounded-md"
              style={{ background: "var(--accent)" }}
            >
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#fffaf7"
                strokeWidth="2.5"
                strokeLinecap="round"
              >
                <path d="M12 2L2 7l10 5 10-5-10-5Z" />
                <path d="m2 17 10 5 10-5" />
                <path d="m2 12 10 5 10-5" />
              </svg>
            </div>
            <span
              className="text-sm font-semibold tracking-tight"
              style={{ color: "var(--text-primary)" }}
            >
              Wren
            </span>
            <span
              className="ml-auto rounded-full px-1.5 py-0.5 text-[9px] font-medium"
              style={{
                background: "var(--accent-subtle)",
                color: "var(--accent-strong)",
              }}
            >
              Free
            </span>
          </header>

          {/* Scrim */}
          {mobileNavOpen && (
            <div
              className="animate-fade-in fixed inset-0 z-40 lg:hidden"
              style={{
                background: "rgba(31,30,29,0.35)",
                backdropFilter: "blur(2px)",
              }}
              onClick={() => setMobileNavOpen(false)}
              aria-hidden="true"
            />
          )}

          {/* Drawer / static sidebar */}
          <aside
            aria-label="Primary"
            role={mobileNavOpen ? "dialog" : undefined}
            aria-modal={mobileNavOpen || undefined}
            className={`fixed inset-y-0 left-0 z-50 flex w-64 shrink-0 transform flex-col border-r transition-transform duration-300 ease-out lg:static lg:z-auto lg:w-60 lg:translate-x-0 ${
              mobileNavOpen ? "translate-x-0" : "-translate-x-full"
            }`}
            style={{
              borderColor: "var(--border)",
              background: "var(--bg-surface)",
              boxShadow: mobileNavOpen ? "var(--shadow-xl)" : "none",
            }}
          >
            {/* Logo */}
            <div
              className="flex h-14 items-center gap-2.5 border-b px-4 pt-0 lg:h-12"
              style={{ borderColor: "var(--border)" }}
            >
              <div
                className="flex h-7 w-7 items-center justify-center rounded-lg text-[9px] font-bold"
                style={{ background: "var(--accent)" }}
              >
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#fffaf7"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                >
                  <path d="M12 2L2 7l10 5 10-5-10-5Z" />
                  <path d="m2 17 10 5 10-5" />
                  <path d="m2 12 10 5 10-5" />
                </svg>
              </div>
              <span
                className="font-display text-base font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                Wren
              </span>
              <span
                className="ml-auto hidden rounded-full px-2 py-0.5 text-[9px] font-medium sm:inline-flex"
                style={{
                  background: "var(--accent-subtle)",
                  color: "var(--accent-strong)",
                }}
              >
                Free
              </span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4 pt-14 lg:pt-4">
              {NAV_ITEMS.map((item) => {
                const isActive = location.pathname === item.to;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    aria-current={isActive ? "page" : undefined}
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-200 ease-out"
                    style={{
                      color: isActive
                        ? "var(--accent-strong)"
                        : "var(--text-secondary)",
                      background: isActive
                        ? "var(--bg-elevated)"
                        : "transparent",
                      boxShadow: isActive ? "var(--shadow-sm)" : "none",
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive)
                        e.currentTarget.style.background =
                          "rgba(31,30,29,0.04)";
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive)
                        e.currentTarget.style.background = "transparent";
                    }}
                  >
                    <span
                      className="flex h-5 w-5 items-center justify-center"
                      style={{ opacity: isActive ? 1 : 0.62 }}
                    >
                      {item.icon}
                    </span>
                    {item.label}
                    {isActive && (
                      <span
                        className="animate-pulse-dot ml-auto h-1.5 w-1.5 rounded-full"
                        style={{ background: "var(--accent)" }}
                      />
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* Bottom status */}
            <div
              className="border-t px-4 py-3"
              style={{ borderColor: "var(--border)" }}
            >
              <div className="flex items-center gap-2 rounded-md px-1 py-1">
                <span
                  className="h-1.5 w-1.5 shrink-0 rounded-full"
                  style={{ background: "var(--status-success)" }}
                />
                <span
                  className="text-[10px] tracking-wide"
                  style={{ color: "var(--text-tertiary)" }}
                >
                  v1.0.0 — Self-hosted
                </span>
              </div>
            </div>
          </aside>
        </>
      )}

      {/* Main Content */}
      <div
        className={`flex min-w-0 flex-1 flex-col ${!isHome ? "pt-12 lg:pt-0" : ""}`}
      >
        <main id="main" className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
