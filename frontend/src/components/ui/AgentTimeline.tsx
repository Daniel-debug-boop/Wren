import { useState } from "react";

interface TimelineEvent {
  id: string;
  type: "action" | "observation" | "message" | "error" | "status";
  actionType?: "run" | "edit" | "think" | "browse" | "task" | string;
  title: string;
  detail?: string;
  timestamp: Date;
  duration?: number;
  status?: "running" | "done" | "error" | "skipped";
}

interface AgentTimelineProps {
  events: TimelineEvent[];
}

const ACTION_ICONS: Record<string, React.ReactNode> = {
  run: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="3 1.5 10 6 3 10.5" />
    </svg>
  ),
  edit: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8.5 1.5l2 2L4 10H2V8l6.5-6.5z" />
    </svg>
  ),
  think: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="4.5" />
      <path d="M6 3.5v2.5l1.5 1.5" />
    </svg>
  ),
  browse: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="4.5" />
      <path d="M6 1.5v9M1.5 6h9" />
    </svg>
  ),
  task: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1.5" y="1.5" width="9" height="9" rx="1.5" />
      <path d="M4 6l1.5 1.5L8 4.5" />
    </svg>
  ),
};

function getIcon(event: TimelineEvent): React.ReactNode {
  if (event.type === "error") {
    return (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
        <circle cx="6" cy="6" r="4.5" />
        <path d="M4.5 4.5l3 3M7.5 4.5l-3 3" />
      </svg>
    );
  }
  if (event.type === "message") {
    return (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M11 6.5a4.5 4.5 0 0 1-4.5 4.5H2l1.5-1.5A4.5 4.5 0 1 1 11 6.5z" />
      </svg>
    );
  }
  return event.actionType ? ACTION_ICONS[event.actionType] ?? ACTION_ICONS.task : ACTION_ICONS.task;
}

function getColor(event: TimelineEvent): string {
  if (event.type === "error") return "var(--diff-del-text)";
  if (event.status === "running") return "var(--accent)";
  if (event.status === "done") return "var(--diff-add-text)";
  if (event.status === "skipped") return "var(--text-quiet)";
  return "var(--text-secondary)";
}

export function AgentTimeline({ events }: AgentTimelineProps) {
  const [collapsed, setCollapsed] = useState(false);

  if (events.length === 0) return null;

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{
        background: "color-mix(in srgb, var(--accent) 3%, var(--surface))",
        border: "1px solid var(--border)",
      }}
    >
      {/* Header */}
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        className="flex w-full items-center justify-between gap-2 px-4 py-2.5 press"
      >
        <div className="flex items-center gap-2">
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            style={{ color: "var(--accent)" }}
          >
            <circle cx="7" cy="7" r="3" />
            <path d="M7 1v2M7 11v2M1 7h2M11 7h2" />
            <path d="M3.5 3.5l1.5 1.5M9 9l1.5 1.5M10.5 3.5L9 5M5 9l-1.5 1.5" />
          </svg>
          <span className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
            Agent Timeline
          </span>
          <span className="text-[10px]" style={{ color: "var(--text-quiet)" }}>
            {events.length} event{events.length > 1 ? "s" : ""}
          </span>
        </div>
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
      </button>

      {/* Events */}
      {!collapsed && (
        <div
          className="flex flex-col px-3 pb-3"
          style={{ borderTop: "1px solid var(--border)" }}
        >
          {events.map((event, idx) => (
            <TimelineRow key={event.id} event={event} isLast={idx === events.length - 1} isFirst={idx === 0} />
          ))}
        </div>
      )}
    </div>
  );
}

function TimelineRow({
  event,
  isLast,
  isFirst,
}: {
  event: TimelineEvent;
  isLast: boolean;
  isFirst: boolean;
}) {
  const [showDetail, setShowDetail] = useState(false);
  const color = getColor(event);

  return (
    <div className="flex gap-3 relative">
      {/* Timeline line + dot */}
      <div className="flex flex-col items-center shrink-0" style={{ width: "20px" }}>
        {!isFirst && (
          <div
            className="w-px flex-1"
            style={{ background: "var(--border)", minHeight: "8px" }}
          />
        )}
        <div
          className="flex h-5 w-5 items-center justify-center rounded-full"
          style={{
            background: "color-mix(in srgb, var(--accent) 8%, transparent)",
            color,
          }}
        >
          {getIcon(event)}
        </div>
        {!isLast && (
          <div
            className="w-px flex-1"
            style={{ background: "var(--border)", minHeight: "8px" }}
          />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-3 pt-0.5">
        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => setShowDetail((d) => !d)}
            className="press text-left"
          >
            <span className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>
              {event.title}
            </span>
          </button>
          <div className="flex items-center gap-1.5 shrink-0">
            {event.duration && (
              <span className="text-[10px]" style={{ color: "var(--text-quiet)" }}>
                {event.duration}ms
              </span>
            )}
            {event.status === "running" && (
              <span className="h-2 w-2 rounded-full animate-pulse-glow" style={{ background: "var(--accent)" }} />
            )}
            {event.status === "done" && (
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="var(--diff-add-text)" strokeWidth="1.5">
                <path d="M2 5l2 2 4-4" />
              </svg>
            )}
            {event.status === "error" && (
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="var(--diff-del-text)" strokeWidth="1.5">
                <path d="M3 3l4 4M7 3l-4 4" />
              </svg>
            )}
          </div>
        </div>

        {showDetail && event.detail && (
          <p className="mt-1 text-[11px] leading-relaxed" style={{ color: "var(--text-subtle)" }}>
            {event.detail}
          </p>
        )}
      </div>
    </div>
  );
}
