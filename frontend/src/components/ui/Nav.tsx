import { Link, useLocation, NavLink } from "react-router";
import { type ReactNode, useEffect, useState } from "react";

interface NavProps {
  children?: ReactNode;
  user?: {
    name: string;
    avatar?: string;
  };
  onSignOut?: () => void;
}

export function Nav({ children, user, onSignOut }: NavProps) {
  const location = useLocation();
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const stored = localStorage.getItem("wren_theme") as
      | "dark"
      | "light"
      | null;
    if (stored) {
      setTheme(stored);
      document.documentElement.classList.toggle("light", stored === "light");
      document.documentElement.classList.toggle("dark", stored === "dark");
    } else if (window.matchMedia("(prefers-color-scheme: light)").matches) {
      setTheme("light");
      document.documentElement.classList.add("light");
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    localStorage.setItem("wren_theme", newTheme);
    document.documentElement.classList.toggle("light", newTheme === "light");
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  };

  const navItems = [
    { path: "/", label: "Conversations" },
    { path: "/pricing", label: "Pricing" },
    { path: "/docs", label: "Docs" },
  ];

  return (
    <nav
      className="fixed top-6 left-1/2 -translate-x-1/2 z-50 w-max"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="flex items-center gap-2 rounded-full bg-surface/80 backdrop-blur-xl border border-border p-1.5 shadow-lg">
        {/* Logo */}
        <Link
          to="/"
          className="nav-item active"
          aria-current={location.pathname === "/" ? "page" : undefined}
        >
          <span
            className="font-semibold text-lg tracking-tight"
            style={{ color: "var(--text)" }}
          >
            Wren
          </span>
        </Link>

        {/* Divider */}
        <div className="w-px h-6 bg-border mx-1" aria-hidden="true" />

        {/* Primary nav items */}
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
            aria-current={location.pathname === item.path ? "page" : undefined}
          >
            {item.label}
          </NavLink>
        ))}

        {/* Custom children (e.g., user actions) */}
        {children}

        {/* Theme toggle */}
        <button
          type="button"
          onClick={toggleTheme}
          className="nav-item"
          aria-label={
            theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
          }
          aria-pressed={theme === "light"}
        >
          {theme === "dark" ? (
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          ) : (
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          )}
        </button>

        {/* User menu */}
        {user && (
          <>
            <div className="w-px h-6 bg-border mx-1" aria-hidden="true" />
            <div className="flex items-center gap-2">
              {user.avatar && (
                <img
                  src={user.avatar}
                  alt=""
                  className="w-7 h-7 rounded-full border border-border"
                  aria-hidden="true"
                />
              )}
              <span
                className="text-sm font-medium hidden sm:block"
                style={{ color: "var(--text)" }}
              >
                {user.name}
              </span>
              {onSignOut && (
                <button
                  onClick={onSignOut}
                  className="btn-ghost px-3 py-1.5 text-xs"
                >
                  Sign out
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </nav>
  );
}

export function NavItem({
  href,
  label,
  isActive,
  onClick,
}: {
  href?: string;
  label: string;
  isActive?: boolean;
  onClick?: () => void;
}) {
  if (href) {
    return (
      <NavLink
        to={href}
        className={({ isActive: active }) =>
          `nav-item ${active || isActive ? "active" : ""}`
        }
        onClick={onClick}
        aria-current={isActive ? "page" : undefined}
      >
        {label}
      </NavLink>
    );
  }

  return (
    <button
      type="button"
      className={`nav-item ${isActive ? "active" : ""}`}
      onClick={onClick}
      aria-current={isActive ? "page" : undefined}
      aria-pressed={isActive}
    >
      {label}
    </button>
  );
}
