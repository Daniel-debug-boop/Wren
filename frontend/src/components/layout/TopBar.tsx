/* ── TopBar — Professional header bar ──
 *  Wren logo · version · mode badge · agent status · Deploy
 */
import { useMode } from "./ModeContext";
import { MODES } from "#/types/mode";

const VERSION = "0.4.2";

interface TopBarProps {
  isRunning?: boolean;
  taskCount?: number;
  elapsedMs?: number;
  onDeploy?: () => void;
}

function formatElapsed(ms: number): string {
  if (!ms) return "0:00";
  const sec = Math.floor(ms / 1000);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function TopBar({
  isRunning = false,
  taskCount = 0,
  elapsedMs = 0,
  onDeploy,
}: TopBarProps) {
  const { mode } = useMode();
  const modeDef = MODES.find((m) => m.id === mode);

  return (
    <header
      className="flex h-11 shrink-0 items-center justify-between border-b px-4"
      style={{
        background: "color-mix(in srgb, var(--surface) 85%, transparent)",
        borderColor: "var(--border)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
      }}
    >
      {/* Left: Logo + Version */}
      <div className="flex items-center gap-2.5">
        {/* Wren logo */}
        <div
          className="flex h-6 w-6 items-center justify-center rounded-md"
          style={{
            background:
              "linear-gradient(135deg, var(--accent), var(--accent-hover))",
            boxShadow:
              "0 0 12px color-mix(in srgb, var(--accent) 20%, transparent)",
          }}
        >
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 2 2 7l10 5 10-5-10-5Z" />
            <path d="m2 17 10 5 10-5" />
            <path d="m2 12 10 5 10-5" />
          </svg>
        </div>

        <span
          className="text-xs font-semibold tracking-tight"
          style={{ color: "var(--text-primary)" }}
        >
          Wren
        </span>

        {/* Version badge */}
        <span
          className="rounded-md px-1.5 py-0.5 text-[9px] font-medium"
          style={{
            background: "rgba(255,255,255,0.05)",
            color: "var(--text-quiet)",
            border: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          v{VERSION}
        </span>
      </div>

      {/* Center: Mode badge + Agent status */}
      <div className="flex items-center gap-3">
        {/* Mode badge */}
        {modeDef && (
          <span
            className="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-medium"
            style={{
              background: "color-mix(in srgb, var(--accent) 10%, transparent)",
              color: "var(--accent)",
              border:
                "1px solid color-mix(in srgb, var(--accent) 15%, transparent)",
            }}
          >
            <span
              className="inline-block h-1.5 w-1.5 rounded-full"
              style={{
                background: "var(--accent)",
                boxShadow: isRunning ? `0 0 6px var(--accent)` : "none",
                animation: isRunning ? "pulse-glow 2s infinite" : "none",
              }}
            />
            {modeDef.shortLabel}
          </span>
        )}

        {/* Agent status pill */}
        <span
          className="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-medium"
          style={{
            background: isRunning
              ? "color-mix(in srgb, var(--accent) 8%, transparent)"
              : "rgba(255,255,255,0.03)",
            color: isRunning ? "var(--accent)" : "var(--text-quiet)",
            border: isRunning
              ? "1px solid color-mix(in srgb, var(--accent) 12%, transparent)"
              : "1px solid rgba(255,255,255,0.04)",
          }}
        >
          <span
            className="inline-block h-1.5 w-1.5 rounded-full"
            style={{
              background: isRunning ? "var(--success)" : "var(--text-quiet)",
              boxShadow: isRunning ? "0 0 6px var(--success)" : "none",
            }}
          />
          {isRunning ? "Agent Active" : "Agent Idle"}
          {taskCount > 0 && (
            <span style={{ color: "var(--text-quiet)" }}>
              {" "}
              &middot; {taskCount} tasks
            </span>
          )}
          {isRunning && elapsedMs > 0 && (
            <span
              className="font-mono"
              style={{ color: "var(--text-quiet)", fontSize: 9 }}
            >
              {" "}
              &middot; {formatElapsed(elapsedMs)}
            </span>
          )}
        </span>
      </div>

      {/* Right: Deploy button */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onDeploy}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-semibold transition-all duration-200"
          style={{
            background:
              "linear-gradient(135deg, var(--accent), var(--accent-hover))",
            color: "white",
            boxShadow:
              "0 0 16px color-mix(in srgb, var(--accent) 25%, transparent), 0 2px 8px rgba(0,0,0,0.3)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translateY(-1px)";
            e.currentTarget.style.boxShadow =
              "0 0 24px color-mix(in srgb, var(--accent) 35%, transparent), 0 4px 12px rgba(0,0,0,0.4)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow =
              "0 0 16px color-mix(in srgb, var(--accent) 25%, transparent), 0 2px 8px rgba(0,0,0,0.3)";
          }}
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M6 2v8M3 7l3 3 3-3" />
          </svg>
          Deploy
        </button>
      </div>
    </header>
  );
}
