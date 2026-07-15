import { useNavigate, useLocation } from "react-router";

export default function SidebarNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const pathname = location.pathname;

  const navItems = [
    {
      id: "chat",
      label: "Chat",
      path: "/",
      icon: (
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="shrink-0"
        >
          <path d="M14 10a2 2 0 0 1-2 2H4l-3 3V3a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v7z" />
        </svg>
      ),
    },
    {
      id: "keys",
      label: "API Keys",
      path: "/api-keys",
      icon: (
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="shrink-0"
        >
          <rect x="2" y="7" width="12" height="7" rx="1.5" />
          <path d="M5 7V4.5a3 3 0 0 1 6 0V7" />
        </svg>
      ),
    },
    {
      id: "settings",
      label: "Settings",
      path: "/settings",
      icon: (
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="shrink-0"
        >
          <circle cx="8" cy="8" r="2.5" />
          <path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.1 3.1l1 1M11.9 11.9l1 1M3.1 12.9l1-1M11.9 4.1l1-1" />
        </svg>
      ),
    },
  ];

  return (
    <div className="flex shrink-0 flex-col gap-0.5 px-3 pb-2 pt-1">
      <nav className="flex flex-col gap-0.5">
        {navItems.map((item) => {
          const isActive =
            item.path === "/"
              ? pathname === "/" || pathname.startsWith("/conversations")
              : pathname.startsWith(item.path);

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => navigate(item.path)}
              className="flex h-8 items-center gap-2.5 rounded-md px-2.5 text-sm font-medium press transition-all duration-200"
              style={{
                background: isActive
                  ? "color-mix(in srgb, var(--glass-accent) 10%, transparent)"
                  : "transparent",
                color: isActive
                  ? "var(--glass-accent)"
                  : "var(--glass-text-secondary)",
              }}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
