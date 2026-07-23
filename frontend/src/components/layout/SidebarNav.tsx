import { useNavigate, useLocation } from "react-router";
import { motion } from "framer-motion";

export default function SidebarNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const { pathname } = location;

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
      id: "skills",
      label: "Skills",
      path: "/skills",
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
          <path d="M7 1l1.5 3L12 4.5 9.5 7l.5 3.5L7 9l-3 1.5L4.5 7 2 4.5 5.5 4 7 1z" />
          <path d="M4 13l3-1.5L10 13l-1-3 2-1.5-3-.5L7 5l-1 3-3 .5L5 10l-1 3z" />
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
      id: "orchestrate",
      label: "Orchestrate",
      path: "/orchestration",
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
          <circle cx="8" cy="8" r="6" />
          <path d="M8 4v4l2.5 1.5" />
          <path d="M5 11c1.5 1 4.5 1 6 0" />
        </svg>
      ),
    },
    {
      id: "generation",
      label: "Generate",
      path: "/generation",
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
          <path d="M12 2H4a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z" />
          <path d="M8 5v6M5 8h6" />
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
      <nav className="flex flex-col gap-1">
        {navItems.map((item, i) => {
          const isActive =
            item.path === "/"
              ? pathname === "/" || pathname.startsWith("/conversations")
              : pathname.startsWith(item.path);

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => navigate(item.path)}
              className="relative flex h-9 items-center gap-2.5 rounded-lg px-2.5 text-sm font-medium press transition-all duration-200 animate-fade-in-up"
              style={{
                color: isActive
                  ? "var(--glass-accent)"
                  : "var(--glass-text-secondary)",
                animationDelay: `${i * 55}ms`,
              }}
            >
              {isActive && (
                <motion.span
                  layoutId="sidebar-nav-active"
                  className="absolute inset-0 rounded-lg"
                  style={{
                    background:
                      "color-mix(in srgb, var(--glass-accent) 12%, transparent)",
                    boxShadow:
                      "inset 0 0 0 1px color-mix(in srgb, var(--glass-accent) 22%, transparent)",
                  }}
                  transition={{ type: "spring", stiffness: 500, damping: 38 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2.5">
                {item.icon}
                <span>{item.label}</span>
              </span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
