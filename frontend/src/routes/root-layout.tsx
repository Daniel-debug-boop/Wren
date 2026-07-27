import { Outlet, Link, useLocation } from "react-router";

/* ── Navigation Items ──────────────────────────────────────────────────────── */

const NAV_ITEMS = [
  {
    to: "/",
    label: "Home",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    to: "/generation",
    label: "Generate",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    ),
  },
  {
    to: "/conversation",
    label: "Chat",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    to: "/settings",
    label: "Settings",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    ),
  },
  {
    to: "/api-keys",
    label: "API Keys",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
      </svg>
    ),
  },
  {
    to: "/skills",
    label: "Skills",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    ),
  },
];

/* ── Layout ────────────────────────────────────────────────────────────────── */

export default function RootLayout() {
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <div className="flex min-h-screen" style={{ background: "var(--color-surface-base)" }}>
      {/* Sidebar — only show for internal pages */}
      {!isHome && (
        <aside
          className="flex w-56 shrink-0 flex-col border-r"
          style={{
            borderColor: "var(--border)",
            background: "color-mix(in srgb, var(--surface) 80%, transparent)",
          }}
        >
          {/* Logo */}
          <div className="flex h-14 items-center gap-2.5 border-b px-4" style={{ borderColor: "var(--border)" }}>
            <div
              className="flex h-7 w-7 items-center justify-center rounded-md"
              style={{ background: "linear-gradient(135deg, var(--accent), var(--accent-hover))" }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2 2 7l10 5 10-5-10-5Z" />
                <path d="m2 17 10 5 10-5" />
                <path d="m2 12 10 5 10-5" />
              </svg>
            </div>
            <span className="text-sm font-bold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
              Wren
            </span>
            <span className="text-[9px] font-medium rounded-full px-1.5 py-0.5 ml-auto" style={{ background: "rgba(45,212,191,0.1)", color: "var(--teal, #2DD4BF)" }}>
              Free
            </span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-0.5 px-2 py-4">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="group flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200"
                style={{
                  color: location.pathname === item.to ? "var(--accent)" : "var(--color-text-tertiary)",
                  background: location.pathname === item.to ? "rgba(139,92,246,0.08)" : "transparent",
                }}
              >
                <span
                  className="transition-transform duration-200 group-hover:scale-110"
                  style={{ opacity: location.pathname === item.to ? 1 : 0.7 }}
                >
                  {item.icon}
                </span>
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Bottom status */}
          <div className="border-t px-3 py-3" style={{ borderColor: "var(--border)" }}>
            <div className="flex items-center gap-2 rounded-lg px-2 py-1.5">
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--teal, #2DD4BF)", boxShadow: "0 0 6px rgba(45,212,191,0.5)" }} />
              <span className="text-[10px]" style={{ color: "var(--color-text-tertiary)" }}>
                All systems operational
              </span>
            </div>
          </div>
        </aside>
      )}

      {/* Main Content */}
      <div className="flex flex-1 flex-col">
        <main id="main" className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
