import { Link } from "react-router";
import { useEffect, useState } from "react";

interface WorkspaceFooterProps {
  artifactsOpen: boolean;
  onToggleArtifacts: () => void;
}

export default function WorkspaceFooter({
  artifactsOpen,
  onToggleArtifacts,
}: WorkspaceFooterProps) {
  const [isDark, setIsDark] = useState(
    () =>
      // Default dark; check stored preference
      localStorage.getItem("wren-theme") !== "light",
  );

  useEffect(() => {
    document.documentElement.classList.toggle("light", !isDark);
    localStorage.setItem("wren-theme", isDark ? "dark" : "light");
  }, [isDark]);

  return (
    <div
      className="flex shrink-0 flex-col px-3 py-2.5"
      style={{
        background: "color-mix(in srgb, var(--glass-accent) 3%, transparent)",
        borderTop: "1px solid var(--glass-border)",
      }}
    >
      {/* Settings & API Keys */}
      <div className="flex items-center gap-1 px-1 pb-2">
        <Link
          to="/settings"
          className="press flex h-7 items-center gap-1.5 rounded-md px-2 text-xs font-medium transition-all duration-200 hover:opacity-80"
          style={{ color: "var(--glass-text-secondary)" }}
        >
          <svg
            width="13"
            height="13"
            viewBox="0 0 13 13"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          >
            <circle cx="6.5" cy="6.5" r="2.5" />
            <path d="M6.5 1v1.5M6.5 10.5V12M1 6.5h1.5M10.5 6.5H12M2.3 2.3l1.1 1.1M9.6 9.6l1.1 1.1M2.3 10.7l1.1-1.1M9.6 3.4l1.1-1.1" />
          </svg>
          <span>Settings</span>
        </Link>
        <Link
          to="/api-keys"
          className="press flex h-7 items-center gap-1.5 rounded-md px-2 text-xs font-medium transition-all duration-200 hover:opacity-80"
          style={{ color: "var(--glass-text-secondary)" }}
        >
          <svg
            width="13"
            height="13"
            viewBox="0 0 13 13"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          >
            <path d="M5.5 7.5l-3 3M6 7l1 1M3 10l-1 1" />
            <circle cx="8.5" cy="4.5" r="3" />
            <path d="M10.5 2.5l1-1" />
          </svg>
          <span>API Keys</span>
        </Link>
        {/* Theme toggle */}
        <button
          type="button"
          onClick={() => setIsDark(!isDark)}
          title={isDark ? "Switch to light mode" : "Switch to dark mode"}
          className="press ml-auto flex h-7 w-7 items-center justify-center rounded-md text-xs transition-all duration-200 hover:opacity-80"
          style={{ color: "var(--glass-text-tertiary)" }}
        >
          {isDark ? (
            <svg
              width="13"
              height="13"
              viewBox="0 0 13 13"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            >
              <circle cx="6.5" cy="6.5" r="3" />
              <path d="M6.5 1v1M6.5 11v1M1 6.5h1M11 6.5h1M2.3 2.3l.7.7M10 10l.7.7M2.3 10.7l.7-.7M10 3l.7-.7" />
            </svg>
          ) : (
            <svg
              width="13"
              height="13"
              viewBox="0 0 13 13"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            >
              <path d="M11 8.5A5 5 0 0 1 4.5 2 5 5 0 1 0 11 8.5z" />
            </svg>
          )}
        </button>
      </div>

      {/* Artifacts toggle */}
      <button
        type="button"
        onClick={onToggleArtifacts}
        className="press flex h-8 items-center gap-2.5 rounded-md px-2.5 text-sm font-medium transition-all duration-200"
        style={{
          color: "var(--glass-text-secondary)",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "var(--claude-hover)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "transparent";
        }}
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 14 14"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        >
          <rect x="1" y="1" width="12" height="12" rx="2" />
          <path d="M5 1v12M9 1v12M1 5h12M1 9h12" />
        </svg>
        <span>{artifactsOpen ? "Hide" : "Artifacts"}</span>
      </button>
    </div>
  );
}
