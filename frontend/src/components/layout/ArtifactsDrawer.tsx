import { useState, useCallback, useEffect, useRef } from "react";
import DOMPurify from "dompurify";
import { useArtifacts } from "./ArtifactsContext";
import { DiffViewRaw } from "#/components/ui/DiffView";

/**
 * Sanitize untrusted agent-provided HTML before rendering it via
 * dangerouslySetInnerHTML. Agent output is untrusted and could carry
 * <script> or event-handler-based XSS.
 */
export function sanitizePreview(html: string): string {
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
}

type TabId = "code" | "diff" | "preview" | "terminal";

interface Tab {
  id: TabId;
  label: string;
}

const TABS: Tab[] = [
  { id: "code", label: "Code" },
  { id: "diff", label: "Diff" },
  { id: "preview", label: "Preview" },
  { id: "terminal", label: "Terminal" },
];

function lineCount(str?: string): number {
  if (!str) return 0;
  return str.split("\n").length;
}

export default function ArtifactsDrawer() {
  const { open, close, data } = useArtifacts();
  const [activeTab, setActiveTab] = useState<TabId>("code");
  const [animState, setAnimState] = useState<
    "closed" | "entering" | "open" | "leaving"
  >(open ? "open" : "closed");
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      setAnimState("entering");
      const raf = requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setAnimState("open");
        });
      });
      return () => cancelAnimationFrame(raf);
    }
    if (animState === "open") {
      setAnimState("leaving");
      const timer = setTimeout(() => {
        setAnimState("closed");
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [open]);

  // Auto-switch to tab when data arrives
  useEffect(() => {
    if (data.diff && activeTab !== "diff" && activeTab !== "terminal") {
      setActiveTab("diff");
    }
  }, [data.diff]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        close();
      }
    },
    [close],
  );

  if (animState === "closed") return null;

  const translateX = animState === "open" ? "0%" : "100%";
  const opacity = animState === "leaving" ? 0 : 1;

  const hasContent = data.code || data.diff || data.preview || data.terminal;

  return (
    <>
      {/* Backdrop (click to close) */}
      {open && (
        <div
          className="fixed inset-0 z-30"
          onClick={close}
          style={{ background: "transparent" }}
        />
      )}

      {/* Drawer Panel (glass-drawer) */}
      <aside
        ref={panelRef}
        role="complementary"
        aria-label="Artifacts panel"
        onKeyDown={handleKeyDown}
        className="glass-drawer relative z-40 flex w-[45%] shrink-0 flex-col transition-all duration-300"
        style={{
          transform: `translateX(${translateX})`,
          opacity,
          transitionTimingFunction: "cubic-bezier(0.22, 1, 0.36, 1)",
        }}
      >
        {/* Left accent glow */}
        <div
          className="pointer-events-none absolute left-0 top-0 h-full w-px"
          style={{
            background: `linear-gradient(180deg, transparent, color-mix(in srgb, var(--glass-accent) 25%, transparent) 50%, transparent)`,
          }}
        />

        {/* ── Tab Header ── */}
        <div
          className="flex shrink-0 items-center px-3"
          style={{
            borderBottom: "1px solid var(--glass-border-strong)",
            height: "44px",
            background:
              "color-mix(in srgb, var(--glass-accent) 2%, transparent)",
          }}
        >
          <div className="flex flex-1 items-center gap-0.5">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className="relative h-7 rounded-md px-3 text-xs font-medium press transition-all duration-200"
                style={{
                  color:
                    activeTab === tab.id
                      ? "var(--glass-accent)"
                      : "var(--glass-text-tertiary)",
                  background:
                    activeTab === tab.id
                      ? "color-mix(in srgb, var(--glass-accent) 10%, transparent)"
                      : "transparent",
                }}
              >
                {activeTab === tab.id && (
                  <span
                    className="absolute bottom-0 left-1/2 h-[2px] w-4 -translate-x-1/2 rounded-full"
                    style={{
                      background: "var(--glass-accent)",
                      bottom: "-1px",
                    }}
                  />
                )}
                {tab.label}
                {tab.id === "diff" && data.diff && (
                  <span
                    className="ml-1 inline-flex h-4 min-w-[1rem] items-center justify-center rounded-full px-1 text-[9px] font-bold"
                    style={{
                      background: "color-mix(in srgb, var(--glass-accent) 20%, transparent)",
                      color: "var(--glass-accent)",
                    }}
                  >
                    !!
                  </span>
                )}
                {tab.id === "terminal" && lineCount(data.terminal) > 1 && (
                  <span
                    className="ml-1 inline-flex h-4 min-w-[1rem] items-center justify-center rounded-full px-1 text-[9px]"
                    style={{
                      background: "color-mix(in srgb, var(--glass-accent) 15%, transparent)",
                      color: "var(--glass-text-tertiary)",
                    }}
                  >
                    {lineCount(data.terminal)}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Close button */}
          <button
            type="button"
            onClick={close}
            aria-label="Close artifacts panel"
            className="press flex h-7 w-7 items-center justify-center rounded-md text-sm transition-colors"
            style={{ color: "var(--glass-text-tertiary)" }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "var(--claude-hover)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            ×
          </button>
        </div>

        {/* ── Content ── */}
        <div className="flex flex-1 flex-col overflow-hidden p-0">
          <div className="flex-1 overflow-auto p-4">
            {!hasContent && (
              <div
                className="flex h-full min-h-[200px] items-center justify-center"
                style={{ color: "var(--glass-text-tertiary)" }}
              >
                <div className="text-center">
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1"
                    className="mx-auto mb-2 opacity-40"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="12" y1="18" x2="12" y2="12" />
                    <line x1="9" y1="15" x2="15" y2="15" />
                  </svg>
                  <p className="text-xs">
                    Agent output will appear here
                  </p>
                  <p className="mt-1 text-[10px] opacity-60">
                    Code diffs, terminal output, and previews
                  </p>
                </div>
              </div>
            )}

            {activeTab === "code" && data.code && (
              <pre
                className="glass rounded-lg p-4 text-sm leading-relaxed overflow-x-auto"
                style={{
                  color: "var(--glass-text-primary)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                <code>{data.code}</code>
              </pre>
            )}

            {activeTab === "diff" && data.diff && (
              <DiffViewRaw diff={data.diff} />
            )}

            {activeTab === "preview" && data.preview && (
              <div
                className="glass flex min-h-[200px] items-center justify-center rounded-lg"
                dangerouslySetInnerHTML={{
                  __html: sanitizePreview(data.preview),
                }}
              />
            )}

            {activeTab === "terminal" && data.terminal && (
              <pre
                className="rounded-lg p-4 text-sm leading-relaxed overflow-x-auto"
                style={{
                  background: "color-mix(in srgb, #000 80%, transparent)",
                  border: "1px solid rgba(160, 240, 160, 0.1)",
                  color: "#a0f0a0",
                  fontFamily: "var(--font-mono)",
                  boxShadow: "inset 0 2px 8px rgba(0,0,0,0.4)",
                }}
              >
                <code>{data.terminal}</code>
              </pre>
            )}
          </div>

          {/* Status bar */}
          <div
            className="flex shrink-0 items-center justify-between px-4 py-2"
            style={{
              borderTop:
                "1px solid color-mix(in srgb, var(--glass-accent) 8%, var(--glass-border))",
              color: "var(--glass-text-tertiary)",
              background:
                "color-mix(in srgb, var(--glass-accent) 2%, transparent)",
              backdropFilter: "blur(8px)",
            }}
          >
            <span className="text-[11px]">
              {activeTab === "code" && `Code · ${lineCount(data.code)} lines`}
              {activeTab === "diff" && data.diff && `Diff · ${lineCount(data.diff)} lines`}
              {activeTab === "preview" && "HTML Preview"}
              {activeTab === "terminal" && `Terminal · ${lineCount(data.terminal)} lines`}
            </span>
            <span
              className="text-[11px] font-medium"
              style={{ color: "var(--glass-accent)" }}
            >
              Artifacts
            </span>
          </div>
        </div>
      </aside>
    </>
  );
}
