import { useState } from "react";
import { Outlet, Link, useLocation } from "react-router";
import { AuthProvider, useAuth } from "#/lib/auth-context";

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

/* ── NavLink Component ─────────────────────────────────────────────────────── */

function NavLink({
  to,
  label,
  icon,
  isActive,
}: {
  to: string;
  label: string;
  icon: React.ReactNode;
  isActive: boolean;
}) {
  return (
    <Link
      to={to}
      className="group flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200"
      style={{
        color: isActive ? "var(--accent)" : "var(--color-text-tertiary)",
        background: isActive ? "rgba(139,92,246,0.08)" : "transparent",
      }}
    >
      <span
        className="transition-transform duration-200 group-hover:scale-110"
        style={{ opacity: isActive ? 1 : 0.7 }}
      >
        {icon}
      </span>
      {label}
    </Link>
  );
}

/* ── Layout Inner ──────────────────────────────────────────────────────────── */

function LayoutInner() {
  const location = useLocation();
  const { isAuthenticated, username, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const isHome = location.pathname === "/";

  // Close user menu on outside click
  const handleBlur = (e: React.FocusEvent) => {
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setShowUserMenu(false);
    }
  };

  return (
    <div className="flex min-h-screen" style={{ background: "var(--color-surface-base)" }}>
      {/* Sidebar — only show for authenticated pages */}
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
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-0.5 px-2 py-4">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                label={item.label}
                icon={item.icon}
                isActive={location.pathname === item.to}
              />
            ))}
          </nav>

          {/* User menu */}
          <div
            className="relative border-t px-2 py-3"
            style={{ borderColor: "var(--border)" }}
            onBlur={handleBlur}
          >
            {isAuthenticated ? (
              <>
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs transition-colors hover:bg-white/5"
                  style={{ color: "var(--color-text-secondary)" }}
                >
                  <div
                    className="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold"
                    style={{ background: "var(--accent)" }}
                  >
                    {username?.charAt(0).toUpperCase() || "U"}
                  </div>
                  <span className="flex-1 truncate text-left">{username || "User"}</span>
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <path d="m6 9 6 6 6-6" />
                  </svg>
                </button>

                {showUserMenu && (
                  <div
                    className="absolute bottom-full left-2 right-2 mb-1 overflow-hidden rounded-lg border shadow-lg"
                    style={{
                      background: "var(--surface)",
                      borderColor: "var(--border)",
                    }}
                  >
                    <Link
                      to="/login"
                      className="block px-3 py-2 text-xs transition-colors hover:bg-white/5"
                      style={{ color: "var(--color-text-secondary)" }}
                    >
                      Account
                    </Link>
                    <button
                      onClick={() => {
                        logout();
                        setShowUserMenu(false);
                      }}
                      className="w-full px-3 py-2 text-left text-xs text-red-400 transition-colors hover:bg-red-500/10"
                    >
                      Sign Out
                    </button>
                  </div>
                )}
              </>
            ) : (
              <Link
                to="/login"
                className="flex items-center justify-center rounded-lg px-3 py-2 text-xs font-medium transition-colors"
                style={{
                  color: "var(--accent)",
                  border: "1px solid var(--accent)",
                }}
              >
                Sign In
              </Link>
            )}
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

/* ── Root Layout (Export) ──────────────────────────────────────────────────── */

export default function RootLayout() {
  return (
    <AuthProvider>
      <LayoutInner />
    </AuthProvider>
  );
}
