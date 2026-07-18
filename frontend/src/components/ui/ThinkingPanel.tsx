/* ── ThinkingPanel - Chain-of-Thought transparency ── */
import { useState, useRef, useEffect } from "react";

export interface ThinkingStep {
  id: string;
  timestamp: number;
  type: "reasoning" | "observation" | "decision" | "tool_call" | "error";
  title: string;
  content: string;
  duration?: number;
}

interface ThinkingPanelProps {
  steps: ThinkingStep[];
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

const STEP_ICONS: Record<ThinkingStep["type"], React.ReactNode> = {
  reasoning: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="4.5" />
      <path d="M6 3.5v2.5l1.5 1.5" />
    </svg>
  ),
  observation: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="4.5" />
      <path d="M6 1.5v9M1.5 6h9" />
    </svg>
  ),
  decision: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="3 1.5 10 6 3 10.5" />
    </svg>
  ),
  tool_call: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1.5" y="4" width="9" height="4" rx="0.8" />
      <path d="M4 2.5l2-1.5 2 1.5M4 9.5l2 1.5 2-1.5" />
    </svg>
  ),
  error: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <circle cx="6" cy="6" r="4.5" />
      <path d="M4.5 4.5l3 3M7.5 4.5l-3 3" />
    </svg>
  ),
};

const STEP_COLORS: Record<ThinkingStep["type"], string> = {
  reasoning: "var(--accent)",
  observation: "var(--diff-add-text)",
  decision: "var(--color-gold-400)",
  tool_call: "var(--text-subtle)",
  error: "var(--diff-del-text)",
};

function formatTime(ts: number): string {
  const d = new Date(ts);
  return d.toLocaleTimeString([], { minute: "2-digit", second: "2-digit", fractionalSecondDigits: 1 });
}

export function ThinkingPanel({ steps, collapsed = false, onToggleCollapse }: ThinkingPanelProps) {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const listRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new steps arrive
  useEffect(() => {
    if (autoScroll && listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [steps.length, autoScroll]);

  // Auto-expand the latest step
  useEffect(() => {
    if (steps.length > 0) {
      setExpandedStep(steps[steps.length - 1].id);
    }
  }, [steps.length]);

  if (steps.length === 0) return null;

  return (
    <div
      className="rounded-xl overflow-hidden transition-all duration-300"
      style={{
        background: "color-mix(in srgb, var(--accent) 2%, var(--surface))",
        border: "1px solid var(--border)",
      }}
    >
      {/* Header */}
      <button
        type="button"
        onClick={onToggleCollapse}
        className="flex w-full items-center justify-between gap-2 px-4 py-2.5 press"
      >
        <div className="flex items-center gap-2">
          {/* Brain icon */}
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            style={{ color: "var(--accent)" }}
          >
            <path d="M7 1.5a2 2 0 00-2 2v7a2 2 0 004 0v-7a2 2 0 00-2-2z" />
            <path d="M4 4.5a3 3 0 01-3 3 3 3 0 003 3" />
            <path d="M10 4.5a3 3 0 013 3 3 3 0 01-3 3" />
            <path d="M5 7h4" />
          </svg>
          <span className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
            Thinking
          </span>
          <span className="text-[10px]" style={{ color: "var(--text-quiet)" }}>
            {steps.length} step{steps.length > 1 ? "s" : ""}
          </span>
          {steps.some((s) => s.type === "reasoning") && (
            <span
              className="inline-flex h-4 items-center rounded-full px-1.5 text-[9px] font-medium"
              style={{
                background: "color-mix(in srgb, var(--accent) 10%, transparent)",
                color: "var(--accent)",
              }}
            >
              CoT
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setAutoScroll((a) => !a);
            }}
            className="press rounded px-1 py-0.5 text-[9px] font-medium"
            style={{
              color: autoScroll ? "var(--accent)" : "var(--text-quiet)",
            }}
            title={autoScroll ? "Auto-scroll on" : "Auto-scroll off"}
          >
            ↓
          </button>
          <svg
            width="10"
            height="10"
            viewBox="0 0 10 10"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            style={{
              color: "var(--text-quiet)",
              transform: collapsed ? "rotate(-90deg)" : "rotate(0deg)",
              transition: "transform 0.2s",
            }}
          >
            <path d="M2.5 3.5l2.5 3 2.5-3" />
          </svg>
        </div>
      </button>

      {/* Steps */}
      {!collapsed && (
        <div
          ref={listRef}
          className="flex flex-col gap-1 px-3 pb-3 overflow-y-auto"
          style={{
            borderTop: "1px solid var(--border)",
            maxHeight: "min(400px, 50vh)",
          }}
          onScroll={(e) => {
            const el = e.currentTarget;
            const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
            if (autoScroll !== atBottom) {
              setAutoScroll(atBottom);
            }
          }}
        >
          {steps.map((step, idx) => {
            const isExpanded = expandedStep === step.id;
            const color = STEP_COLORS[step.type];
            const isLast = idx === steps.length - 1;

            return (
              <div key={step.id} className="flex gap-2">
                {/* Timeline */}
                <div className="flex flex-col items-center shrink-0" style={{ width: "16px" }}>
                  <div
                    className="flex h-4 w-4 items-center justify-center rounded-full shrink-0"
                    style={{
                      background: `color-mix(in srgb, ${color} 10%, transparent)`,
                      color,
                    }}
                  >
                    {STEP_ICONS[step.type]}
                  </div>
                  {!isLast && (
                    <div
                      className="w-px flex-1 min-h-[8px]"
                      style={{ background: "var(--border)" }}
                    />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 pb-2">
                  <button
                    type="button"
                    onClick={() => setExpandedStep(isExpanded ? null : step.id)}
                    className="w-full text-left press group"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[11px] font-medium" style={{ color: "var(--text-primary)" }}>
                        {step.title}
                      </span>
                      <div className="flex items-center gap-1.5 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="text-[9px]" style={{ color: "var(--text-quiet)" }}>
                          {formatTime(step.timestamp)}
                        </span>
                        {step.duration !== undefined && (
                          <span className="text-[9px]" style={{ color: "var(--text-quiet)" }}>
                            {step.duration}ms
                          </span>
                        )}
                      </div>
                    </div>
                  </button>

                  {isExpanded && step.content && (
                    <div
                      className="mt-1 rounded-lg p-2 text-[11px] leading-relaxed whitespace-pre-wrap"
                      style={{
                        background: "color-mix(in srgb, var(--surface) 60%, transparent)",
                        border: "1px solid var(--border)",
                        color: "var(--text-subtle)",
                      }}
                    >
                      {step.content}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
